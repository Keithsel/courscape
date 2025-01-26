from loguru import logger
import requests
import json
from pathlib import Path


class CourseraAPIClient:
    """Handle all API interactions with Coursera"""

    BASE_URL = "https://www.coursera.org/api/"
    GRAPHQL_URL = "https://www.coursera.org/graphql-gateway"
    GRAPHQL_WRAPPER_URL = "https://www.coursera.org/graphql-gateway-wrapper"

    def __init__(self, cookies):
        self.session = requests.Session()
        self._setup_session(cookies)

    def _setup_session(self, cookies):
        """Initialize session with cookies"""
        if isinstance(cookies, (str, Path)):
            with open(cookies) as f:
                cookies = json.load(f)
        for cookie in cookies:
            self.session.cookies.set(
                cookie["name"], cookie["value"], domain=cookie["domain"]
            )

    def get_user_id(self):
        """Get user ID from Coursera API"""
        try:
            response = self.session.get(f"{self.BASE_URL}adminUserPermissions.v1?q=my")
            return response.json()["elements"][0]["id"]
        except Exception as e:
            logger.error(f"Error getting user ID: {str(e)}")
            return None

    def get_course_data(self, course_slug):
        """Get course structure and content in one request"""
        params = {
            "q": "slug",
            "slug": course_slug,
            "includes": "modules,lessons,items",
            "fields": ",".join(
                [
                    # It's better not to trim too much from the original query
                    # as it may lead to failed requests.
                    # Actually I don't think removx ing the parameters does anything
                    # since the API will return the same data regardless.
                    "onDemandCourseMaterialModules.v1(name,slug,description,timeCommitment,lessonIds,optional,learningObjectives),"
                    "onDemandCourseMaterialLessons.v1(name,slug,timeCommitment,elementIds,optional,trackId),"
                    "onDemandCourseMaterialItems.v2(name,originalName,slug,timeCommitment,contentSummary,isLocked,lockableByItem,itemLockedReasonCode,trackId,lockedStatus,itemLockSummary),"
                    "contentAtomRelations.v1(embeddedContentSourceCourseId,subContainerId)"
                ]
            ),
            "showLockedItems": "true",
        }
        return self._make_request(
            "GET", f"{self.BASE_URL}onDemandCourseMaterials.v2/", params=params
        )

    def _make_request(self, method, url, **kwargs):
        """Centralized request handling with error handling and logging"""
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API request failed: {url} - {str(e)}")
            return None

    def get_specialization_courses(self, spec_slug):
        """Get all courses in a specialization"""
        try:
            # Step 1: Get specialization ID
            params = {"opname": "GetSpecializationBySlugForPromotionBanner"}
            json_data = [
                {
                    "operationName": "GetSpecializationBySlugForPromotionBanner",
                    "variables": {"slug": spec_slug},
                    "query": "query GetSpecializationBySlugForPromotionBanner($slug: String!) {\n  Specialization {\n    queryBySlug(slug: $slug) {\n      id\n      courses {\n        id\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",
                }
            ]

            response = self.session.post(
                self.GRAPHQL_URL, params=params, json=json_data
            )
            spec_id = response.json()[0]["data"]["Specialization"]["queryBySlug"]["id"]

            # Step 2: Get courses using spec ID
            params = {"opname": "OnDemandSpecializations"}
            json_data = [
                {
                    "operationName": "OnDemandSpecializations",
                    "variables": {"id": spec_id},
                    "query": "query OnDemandSpecializations($id: String!) {\n  OnDemandSpecializationsV1Resource {\n    get(id: $id) {\n      courses {\n        elements {\n          slug\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",
                }
            ]

            response = self.session.post(
                self.GRAPHQL_WRAPPER_URL, params=params, json=json_data
            )
            courses = response.json()[0]["data"]["OnDemandSpecializationsV1Resource"][
                "get"
            ]["courses"]["elements"]
            return [course["slug"] for course in courses if course.get("slug")]

        except Exception as e:
            logger.error(f"Error getting specialization courses: {str(e)}")
            return []

    def mark_lecture_complete(self, user_id, course_slug, item_id):
        """Mark a lecture as completed - uses course slug"""
        logger.debug(f"Marking lecture complete: {item_id}")
        try:
            response = self.session.post(
                f"{self.BASE_URL}opencourse.v1/user/{user_id}/course/{course_slug}/item/{item_id}/lecture/videoEvents/ended",
                params={"autoEnroll": "false"},
                json={"contentRequestBody": {}},
            )
            data = response.json()
            return data.get("itemProgress", {}).get("progressState") == "Completed"
        except Exception as e:
            logger.error(f"Error marking lecture complete: {str(e)}")
            return False

    def get_module_items(self, module_id):
        """Get items for a specific module"""
        logger.debug(f"Fetching items for module: {module_id}")
        try:
            response = self.session.get(
                f"{self.BASE_URL}onDemandCourseMaterialItems.v2/",
                params={"moduleId": module_id},
            )
            return response.json().get("elements", [])
        except Exception as e:
            logger.error(f"Error getting module items: {str(e)}")
            return []

    def mark_supplement_complete(self, course_id, item_id, user_id):
        """Mark a supplement or discussion as completed - uses course ID"""
        try:
            response = self.session.post(
                f"{self.BASE_URL}onDemandSupplementCompletions.v1",
                json={"courseId": course_id, "itemId": item_id, "userId": int(user_id)},
            )
            return "Completed" in response.text
        except Exception as e:
            logger.error(f"Error marking supplement complete: {str(e)}")
            return False

    def get_discussion_question_id(self, user_id, course_id, item_id):
        """Get the question ID for a discussion prompt - uses course ID"""
        try:
            params = {
                "fields": "onDemandDiscussionPromptQuestions.v1(id)",
                "includes": "question",
            }
            response = self.session.get(
                f"{self.BASE_URL}onDemandDiscussionPrompts.v1/{user_id}~{course_id}~{item_id}",
                params=params,
            )
            data = response.json()
            if (
                "linked" in data
                and "onDemandDiscussionPromptQuestions.v1" in data["linked"]
            ):
                return data["linked"]["onDemandDiscussionPromptQuestions.v1"][0][
                    "id"
                ].split("~")[-1]
            return None
        except Exception as e:
            logger.error(f"Error getting discussion question ID: {str(e)}")
            return None

    def skip_discussion(self, course_id, item_id, user_id):
        """Submit minimal response to skip discussion - uses course ID"""
        logger.debug(f"Skipping discussion: {item_id}")
        try:
            # Get the question ID
            question_id = self.get_discussion_question_id(user_id, course_id, item_id)
            if not question_id:
                return False

            # Submit the answer
            response = self.session.post(
                f"{self.BASE_URL}onDemandCourseForumAnswers.v1/",
                json={
                    "content": {
                        "typeName": "cml",
                        "definition": {
                            "dtdId": "discussion/1",
                            "value": "<co-content><text>abc</text></co-content>",
                        },
                    },
                    "courseForumQuestionId": f"{course_id}~{question_id}",
                },
            )
            return response.ok
        except Exception as e:
            logger.error(f"Error skipping discussion: {str(e)}")
            return False

    def bypass_item(self, item_id, item_type, course_id, course_slug, user_id):
        """Unified method to bypass any item type"""
        try:
            if item_type == "lecture":
                return self.mark_lecture_complete(user_id, course_slug, item_id)
            elif item_type == "discussionPrompt":
                return self.skip_discussion(course_id, item_id, user_id)
            elif item_type == "supplement":
                return self.mark_supplement_complete(course_id, item_id, user_id)
            return False
        except Exception as e:
            logger.error(f"Error bypassing {item_type}: {str(e)}")
            return False
