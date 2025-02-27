import json
import os
from datetime import datetime
from pathlib import Path
from loguru import logger


class ProgressTracker:
    """Manage content maps and progress tracking"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.progress_dir = Path("progress") / str(user_id)
        self.progress_dir.mkdir(parents=True, exist_ok=True)
        (self.progress_dir / "courses").mkdir(exist_ok=True)
        (self.progress_dir / "specs").mkdir(exist_ok=True)
        self.current_progress = None
        self.current_file_path = None
    
    def get_progress_file_path(self, course_slug, spec_slug=None):
        """Get the path to the progress file for a course or specialization"""
        if spec_slug:
            # For specs: progress/{user_id}/specs/{spec_slug}/{course_slug}.json
            path = self.progress_dir / "specs" / spec_slug
            path.mkdir(exist_ok=True)
            return path / f"{course_slug}.json"
        # For courses: progress/{user_id}/courses/{course_slug}.json
        return self.progress_dir / "courses" / f"{course_slug}.json"
    
    def load_progress(self, course_slug, spec_slug=None):
        """Load progress from file if it exists"""
        self.current_file_path = self.get_progress_file_path(course_slug, spec_slug)
        if self.current_file_path.exists():
            try:
                with open(self.current_file_path, "r") as f:
                    self.current_progress = json.load(f)
                    logger.info(f"Loaded existing progress for {course_slug}")
                    return self.current_progress
            except Exception as e:
                logger.error(f"Error loading progress file: {str(e)}")
        
        return None
    
    def create_content_map(self, course_slug, course_data, skippable_types):
        """Create a new content map from course data"""
        linked = course_data.get("linked", {})
        modules = linked.get("onDemandCourseMaterialModules.v1", [])
        lessons = {l["id"]: l for l in linked.get("onDemandCourseMaterialLessons.v1", [])}
        items = {i["id"]: i for i in linked.get("onDemandCourseMaterialItems.v2", [])}
        
        content_map = {
            "user_id": self.user_id,
            "course_slug": course_slug,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "modules": []
        }
        
        for module in modules:
            module_data = {
                "id": module["id"],
                "name": module["name"],
                "lessons": []
            }
            
            for lesson_id in module.get("lessonIds", []):
                lesson = lessons.get(lesson_id)
                if not lesson:
                    continue
                    
                lesson_data = {
                    "id": lesson["id"],
                    "name": lesson["name"],
                    "items": []
                }
                
                for item_id in lesson.get("itemIds", []):
                    item = items.get(item_id)
                    if not item:
                        continue
                        
                    item_type = item.get("contentSummary", {}).get("typeName", "unknown")
                    skippable = item_type in skippable_types
                    
                    item_data = {
                        "id": item["id"],
                        "name": item.get("name", "Unnamed"),
                        "type": item_type,
                        "skippable": skippable
                    }
                    
                    if skippable:
                        item_data["status"] = "queued"
                        
                    lesson_data["items"].append(item_data)
                
                if lesson_data["items"]:
                    module_data["lessons"].append(lesson_data)
            
            if module_data["lessons"]:
                content_map["modules"].append(module_data)
        
        self.current_progress = content_map
        return content_map
    
    def save_progress(self):
        """Save current progress to file"""
        if not self.current_progress or not self.current_file_path:
            logger.warning("No progress to save")
            return False
            
        try:
            self.current_progress["updated_at"] = datetime.now().isoformat()
            with open(self.current_file_path, "w") as f:
                json.dump(self.current_progress, f, indent=2)
            logger.debug(f"Progress saved to {self.current_file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving progress: {str(e)}")
            return False
    
    def update_item_status(self, item_id, status):
        """Update the status of an item"""
        if not self.current_progress:
            logger.warning("No progress loaded")
            return False
            
        for module in self.current_progress.get("modules", []):
            for lesson in module.get("lessons", []):
                for item in lesson.get("items", []):
                    if item.get("id") == item_id and item.get("skippable", False):
                        item["status"] = status
                        return True
        
        return False
    
    def get_queued_items(self):
        """Get all queued items that need processing"""
        queued_items = []
        
        if not self.current_progress:
            logger.warning("No progress loaded")
            return queued_items
            
        for module in self.current_progress.get("modules", []):
            for lesson in module.get("lessons", []):
                for item in lesson.get("items", []):
                    if item.get("skippable", False) and item.get("status", "") == "queued":
                        queued_items.append(item)
        
        return queued_items
    
    def get_progress_summary(self):
        """Get a summary of the current progress"""
        if not self.current_progress:
            return None
            
        total = 0
        completed = 0
        queued = 0
        failed = 0
        
        for module in self.current_progress.get("modules", []):
            for lesson in module.get("lessons", []):
                for item in lesson.get("items", []):
                    if item.get("skippable", False):
                        total += 1
                        status = item.get("status", "")
                        if status == "completed":
                            completed += 1
                        elif status == "queued":
                            queued += 1
                        elif status == "failed":
                            failed += 1
        
        return {
            "total_skippable": total,
            "completed": completed,
            "queued": queued,
            "failed": failed,
            "progress_percent": (completed / total * 100) if total > 0 else 0
        }

    def update_skippable_status(self, skippable_types):
        """Update which items are skippable based on current configuration"""
        if not self.current_progress:
            logger.warning("No progress loaded to update")
            return False
            
        updates_made = False
        
        for module in self.current_progress.get("modules", []):
            for lesson in module.get("lessons", []):
                for item in lesson.get("items", []):
                    item_type = item.get("type", "unknown")
                    currently_skippable = item.get("skippable", False)
                    should_be_skippable = item_type in skippable_types
                    
                    # If skippability changed
                    if currently_skippable != should_be_skippable:
                        item["skippable"] = should_be_skippable
                        updates_made = True
                        
                        # If newly skippable, set status to queued
                        if should_be_skippable and "status" not in item:
                            item["status"] = "queued"
        
        if updates_made:
            logger.info("Updated skippable status for items based on current configuration")
            return self.save_progress()
        
        return True
