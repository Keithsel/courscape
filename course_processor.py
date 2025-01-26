from loguru import logger
from api_client import CourseraAPIClient


class CourseProcessor:
    """Handle course content processing"""

    BYPASS_TYPES = {"lecture", "discussionPrompt", "supplement"}
    WORK_LATER_TYPES = {
        "exam",
        "gradedLti",
        "gradedProgramming",
        "peer",
        "phasedPeer",
        "staffGraded",
        "ungradedLti",
        "ungradedProgramming",
    }

    def __init__(self, cookies):
        self.api = CourseraAPIClient(cookies)
        self.user_id = None
        self.course_id = None
        self.course_slug = None
        self.skip_list = {"courses": set(), "specializations": set()}

    def setup(self, skip_courses=None, skip_specs=None):
        """Initialize processor"""
        self.user_id = self.api.get_user_id()
        if skip_courses:
            self.skip_list["courses"].update(
                c.strip() for c in skip_courses if c.strip()
            )
        if skip_specs:
            self.skip_list["specializations"].update(
                s.strip() for s in skip_specs if s.strip()
            )
        return bool(self.user_id)

    def process_content(self, course_slug=None, spec_slug=None):
        """Main entry point for processing content"""
        if spec_slug:
            if spec_slug in self.skip_list["specializations"]:
                logger.info(f"Skipping specialization: {spec_slug}")
                return False
            return self._process_specialization(spec_slug)

        if course_slug:
            if course_slug in self.skip_list["courses"]:
                logger.info(f"Skipping course: {course_slug}")
                return False
            return self._process_course(course_slug)

    def _process_specialization(self, spec_slug):
        """Process all courses in a specialization"""
        logger.info(f"\n[Specialization] {spec_slug}")
        course_slugs = self.api.get_specialization_courses(spec_slug)

        if not course_slugs:
            logger.error("No courses found in specialization")
            return False

        logger.info(f"Found {len(course_slugs)} courses")
        for i, course_slug in enumerate(course_slugs, 1):
            logger.info(f"  Course {i}/{len(course_slugs)}: {course_slug}")
            self._process_course(course_slug)
        return True

    def _process_course(self, course_slug):
        """Process a single course"""
        course_data = self.api.get_course_data(course_slug)
        if not course_data or "elements" not in course_data:
            logger.error(f"Failed to get course data for {course_slug}")
            return False

        # Store both slug and ID as they're used in different endpoints
        self.course_slug = course_slug
        self.course_id = course_data["elements"][0]["id"]
        return self._process_course_content(course_data)

    def _process_course_content(self, course_data):
        """Process course content hierarchically"""
        linked = course_data.get("linked", {})
        modules = linked.get("onDemandCourseMaterialModules.v1", [])
        lessons = {
            l["id"]: l for l in linked.get("onDemandCourseMaterialLessons.v1", [])
        }
        items = {i["id"]: i for i in linked.get("onDemandCourseMaterialItems.v2", [])}

        if not modules:
            logger.error("No modules found in course data")
            return False

        # Show structure overview
        logger.debug(
            f"Found {len(modules)} modules, {len(lessons)} lessons, {len(items)} items"
        )
        logger.info("Starting content processing...")

        for i, module in enumerate(modules, 1):
            logger.info(f"    [Module {i}/{len(modules)}] {module['name']}")
            self._process_module_content(module, lessons, items)
        return True

    def _process_module_content(self, module, lessons, items):
        """Process content within a module"""
        for lesson_id in module.get("lessonIds", []):
            lesson = lessons.get(lesson_id)
            if not lesson:
                continue

            logger.info(f"      [Lesson] {lesson['name']}")
            for item_id in lesson.get("itemIds", []):
                if item := items.get(item_id):
                    self._process_item(item)

    def _process_item(self, item):
        """Process a single content item"""
        item_type = item.get("contentSummary", {}).get("typeName")
        if not item_type:
            logger.warning(f"No type found for item {item.get('name', 'Unknown')}")
            return False

        name = item.get("name", "Unnamed")
        if item_type in self.BYPASS_TYPES:
            # Pass both slug and id - let API client decide which to use
            success = self.api.bypass_item(
                item["id"], item_type, self.course_id, self.course_slug, self.user_id
            )
            status = "✓" if success else "✗"
            if success:
                logger.info(f"        {status} [{item_type}] {name}")
            else:
                logger.error(f"        {status} Failed to process [{item_type}] {name}")
            logger.debug(f"Item details - Type: {item_type}, ID: {item['id']}")
            return success
        elif item_type in self.WORK_LATER_TYPES:
            logger.info(f"        ⚠ Work later: [{item_type}] {name}")
            return True
        return False

    def close(self):
        """Clean up resources"""
        if hasattr(self, "api"):
            self.api.session.close()
