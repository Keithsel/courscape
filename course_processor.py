from loguru import logger
from api_client import CourseraAPIClient
from progress_tracker import ProgressTracker


class CourseProcessor:
    """Handle course content processing"""

    BYPASS_TYPES = {"lecture", "supplement", "ungradedWidget"}
    WORK_LATER_TYPES = {
        "exam",
        "gradedLti",
        "gradedProgramming",
        "peer",
        "phasedPeer",
        "staffGraded",
        "ungradedAssignment",
        "ungradedLti",
        "ungradedProgramming",
        "discussionPrompt"
    }

    def __init__(self, cookies):
        self.api = CourseraAPIClient(cookies)
        self.user_id = None
        self.course_id = None
        self.course_slug = None
        self.spec_slug = None
        self.skip_list = {"courses": set(), "specializations": set()}
        self.progress_tracker = None

    def get_skippable_types(cls):
        """Return the current skippable content types"""
        return cls.BYPASS_TYPES.copy()
        
    def get_work_later_types(cls):
        """Return the current work-later content types"""
        return cls.WORK_LATER_TYPES.copy()

    def setup(self, skip_courses=None, skip_specs=None):
        """Initialize processor"""
        self.user_id = self.api.get_user_id()
        if not self.user_id:
            logger.error("Failed to get user ID")
            return False
            
        self.progress_tracker = ProgressTracker(self.user_id)
        
        if skip_courses:
            self.skip_list["courses"].update(
                c.strip() for c in skip_courses if c.strip()
            )
        if skip_specs:
            self.skip_list["specializations"].update(
                s.strip() for s in skip_specs if s.strip()
            )
        return True

    def process_content(self, course_slug=None, spec_slug=None):
        """Main entry point for processing content"""
        self.spec_slug = spec_slug
        
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
        success_count = 0
        for i, course_slug in enumerate(course_slugs, 1):
            logger.info(f"  Course {i}/{len(course_slugs)}: {course_slug}")
            if self._process_course(course_slug):
                success_count += 1
                
        return success_count > 0

    def _process_course(self, course_slug):
        """Process a single course"""
        course_data = self.api.get_course_data(course_slug)
        if not course_data or "elements" not in course_data:
            logger.error(f"Failed to get course data for {course_slug}")
            return False

        # Store both slug and ID as they're used in different endpoints
        self.course_slug = course_slug
        self.course_id = course_data["elements"][0]["id"]
        
        # Load existing progress or create new content map
        existing_progress = self.progress_tracker.load_progress(course_slug, self.spec_slug)
        
        if existing_progress:
            # Update skippable status if content type classifications have changed
            self.progress_tracker.update_skippable_status(self.BYPASS_TYPES)
            
            # Process based on existing progress
            summary = self.progress_tracker.get_progress_summary()
            if summary:
                logger.info(f"Progress: {summary['completed']}/{summary['total_skippable']} completed ({summary['progress_percent']:.1f}%)")
                
            if summary and summary["queued"] > 0:
                return self._process_queued_items()
            elif summary and summary["queued"] == 0:
                logger.success(f"Course already completed: {course_slug}")
                return True
        else:
            # Create a new content map
            self.progress_tracker.create_content_map(course_slug, course_data, self.BYPASS_TYPES)
            self.progress_tracker.save_progress()
            return self._process_course_content(course_data)

    def _process_queued_items(self):
        """Process only queued items from progress tracker"""
        queued_items = self.progress_tracker.get_queued_items()
        logger.info(f"Processing {len(queued_items)} queued items")
        
        success_count = 0
        for i, item in enumerate(queued_items, 1):
            logger.info(f"  Item {i}/{len(queued_items)}: {item['name']} ({item['type']})")
            
            # Update status to processing
            self.progress_tracker.update_item_status(item['id'], "processing")
            self.progress_tracker.save_progress()
            
            # Process the item
            success = self.api.bypass_item(
                item['id'], item['type'], self.course_id, self.course_slug, self.user_id
            )
            
            # Update status based on result
            status = "completed" if success else "failed"
            self.progress_tracker.update_item_status(item['id'], status)
            self.progress_tracker.save_progress()
            
            if success:
                logger.success(f"    ✓ Completed {item['name']}")
                success_count += 1
            else:
                logger.error(f"    ✗ Failed {item['name']}")
                
        summary = self.progress_tracker.get_progress_summary()
        logger.info(f"Updated progress: {summary['completed']}/{summary['total_skippable']} completed ({summary['progress_percent']:.1f}%)")
        return success_count > 0

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
            
        summary = self.progress_tracker.get_progress_summary()
        if summary:
            logger.info(f"Final progress: {summary['completed']}/{summary['total_skippable']} completed ({summary['progress_percent']:.1f}%)")
        
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
        item_id = item["id"]
        
        if item_type in self.BYPASS_TYPES:
            # Update status to processing
            self.progress_tracker.update_item_status(item_id, "processing")
            self.progress_tracker.save_progress()
            
            # Pass both slug and id - let API client decide which to use
            success = self.api.bypass_item(
                item_id, item_type, self.course_id, self.course_slug, self.user_id
            )
            
            # Update status based on result
            status = "completed" if success else "failed"
            self.progress_tracker.update_item_status(item_id, status)
            self.progress_tracker.save_progress()
            
            status_icon = "✓" if success else "✗"
            if success:
                logger.info(f"        {status_icon} [{item_type}] {name}")
            else:
                logger.error(f"        {status_icon} Failed to process [{item_type}] {name}")
                
            logger.debug(f"Item details - Type: {item_type}, ID: {item_id}")
            return success
        elif item_type in self.WORK_LATER_TYPES:
            logger.info(f"        ⚠ Work later: [{item_type}] {name}")
            return True
        return False

    def close(self):
        """Clean up resources"""
        if hasattr(self, "api"):
            self.api.session.close()
