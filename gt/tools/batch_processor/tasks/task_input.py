"""
Batch Processor Input Task
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_task_base as task_base
import gt.ui.resource_library as ui_res_lib
import fnmatch
import glob
import os


class TaskInput(task_base.BatchTask):
    """Task responsible for discovering source files."""

    task_type = constants.TaskType.INPUT
    default_display_name = "Input Files"
    icon = ui_res_lib.Icon.batch_task_import_file
    category = "Inputs"
    category_icon = ui_res_lib.Icon.batch_category_inputs
    default_segment_name = "New Input Segment"
    is_input_task = True

    def _normalize_common_settings(self, incoming_settings=None):
        """Normalizes input settings and removes the retired explicit-ignore option.

        Args:
            incoming_settings (dict, optional): Raw settings supplied to the task.
        """
        super()._normalize_common_settings(incoming_settings=incoming_settings)
        self.settings.pop("explicit_ignore_patterns", None)

    def get_default_settings(self):
        """Gets default input settings.

        Returns:
            dict: Default input task settings.
        """
        return {
            "include_in_task_index": False,
            "source_path": "{project-dir}/{input-dir}",
            "include_subdirectories": True,
            "extensions": [".ma", ".mb", ".fbx"],
            "exclude_patterns": [],
            "explicit_files": [],
            "start_new_input_list": False,
            "force_segment_separator": False,
            "segment_name": "",
            "segment_color": "blue_light_sky",
        }

    def get_source_path_template(self):
        """Gets this input task's source path template.

        Returns:
            str: Source path template.
        """
        default_source_path = "{project-dir}/{input-dir}"
        source_path = self.settings.get("source_path")
        legacy_input_path = self.settings.get("input_path") or self.settings.get("input_dir")
        if legacy_input_path and (not source_path or source_path == default_source_path):
            return legacy_input_path
        return source_path or legacy_input_path or default_source_path

    def get_task_path_template(self):
        """Gets the path represented by this input task.

        Returns:
            str: Input source path template.
        """
        return self.get_source_path_template()

    def get_input_dir(self, project):
        """Gets the resolved input directory.

        Args:
            project (BatchProcessorModel): Active project model.

        Returns:
            str: Resolved input directory path.
        """
        return project.resolve_template_path(self.get_source_path_template(), task=self)

    def validate(self, project):
        """Validates input discovery settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        explicit_files = self.settings.get("explicit_files") or []
        input_dir = self.get_input_dir(project)
        if not explicit_files and not os.path.isdir(input_dir):
            result.add_error("Input directory does not exist: {0}".format(input_dir))
        unresolved_files = self.get_unresolved_explicit_file_entries(project)
        if unresolved_files:
            result.add_warning("Explicit input file entries did not resolve: {0}".format(len(unresolved_files)))
        return result

    def discover_files(self, project):
        """Discovers input files using this task's settings.

        Args:
            project (BatchProcessorModel): Active project model.

        Returns:
            list: Sorted normalized file paths.
        """
        explicit_files = self.settings.get("explicit_files") or []
        if explicit_files:
            return self.resolve_explicit_files(project)

        input_dir = self.get_input_dir(project)
        if not os.path.isdir(input_dir):
            return []

        include_subdirectories = bool(self.settings.get("include_subdirectories", True))
        discovered = []
        if include_subdirectories:
            walker = os.walk(input_dir)
        else:
            walker = [(input_dir, [], os.listdir(input_dir))]

        for root, _, file_names in walker:
            for file_name in file_names:
                file_path = os.path.join(root, file_name)
                if os.path.isfile(file_path) and self._is_file_allowed(file_path):
                    discovered.append(task_base.normalize_path(file_path))
        return sorted(set(discovered))

    def resolve_explicit_files(self, project):
        """Resolves explicit file entries into concrete file paths.

        Explicit entries can be absolute paths, project/template paths, paths
        relative to the input folder, file names, or wildcard expressions.

        Args:
            project (BatchProcessorModel): Active project model.

        Returns:
            list: Sorted normalized file paths.
        """
        explicit_files = self.settings.get("explicit_files") or []
        folder_files = self.discover_folder_files(project)
        discovered = []
        for explicit_entry in explicit_files:
            discovered.extend(
                self.resolve_explicit_file_entry(
                    explicit_entry=explicit_entry,
                    project=project,
                    folder_files=folder_files,
                )
            )
        return sorted(set(discovered))

    def get_unresolved_explicit_file_entries(self, project):
        """Gets explicit entries that do not resolve to any accepted file.

        Args:
            project (BatchProcessorModel): Active project model.

        Returns:
            list: Explicit entries that resolved to no file paths.
        """
        explicit_files = self.settings.get("explicit_files") or []
        folder_files = self.discover_folder_files(project)
        unresolved_entries = []
        for explicit_entry in explicit_files:
            resolved_files = self.resolve_explicit_file_entry(
                explicit_entry=explicit_entry,
                project=project,
                folder_files=folder_files,
            )
            if not resolved_files:
                unresolved_entries.append(explicit_entry)
        return unresolved_entries

    def resolve_explicit_file_entry(self, explicit_entry, project, folder_files=None):
        """Resolves one explicit file entry into concrete file paths.

        Args:
            explicit_entry (str): User-provided explicit file entry.
            project (BatchProcessorModel): Active project model.
            folder_files (list, optional): Pre-discovered input-folder files.

        Returns:
            list: Sorted normalized file paths matched by the entry.
        """
        explicit_entry = str(explicit_entry or "").strip()
        if not explicit_entry:
            return []

        discovered = []
        for path_candidate in self._get_explicit_path_candidates(explicit_entry, project):
            discovered.extend(self._resolve_path_candidate(path_candidate))

        folder_files = folder_files if folder_files is not None else self.discover_folder_files(project)
        input_dir = self.get_input_dir(project)
        project_dir = project.get_project_dir() if project and hasattr(project, "get_project_dir") else ""
        match_patterns = self._get_explicit_match_patterns(explicit_entry, project)
        for file_path in folder_files:
            if not self._is_file_allowed(file_path):
                continue
            if self._explicit_entry_matches_file(
                file_path=file_path,
                patterns=match_patterns,
                input_dir=input_dir,
                project_dir=project_dir,
            ):
                discovered.append(task_base.normalize_path(file_path))

        return sorted(set([path for path in discovered if self._is_file_allowed(path)]))

    def get_file_statistics(self, project):
        """Gets file statistics for this input task.

        Args:
            project (BatchProcessorModel): Active project model.

        Returns:
            dict: File statistics for resolved files and source folder contents.
        """
        resolved_files = self.discover_files(project)
        folder_files = self.discover_folder_files(project)
        extension_counts = {}
        resolved_extension_counts = {}
        for file_path in folder_files:
            extension = os.path.splitext(file_path)[1].lower() or "<no extension>"
            extension_counts[extension] = extension_counts.get(extension, 0) + 1
        for file_path in resolved_files:
            extension = os.path.splitext(file_path)[1].lower() or "<no extension>"
            resolved_extension_counts[extension] = resolved_extension_counts.get(extension, 0) + 1
        return {
            "resolved_count": len(resolved_files),
            "total_count": len(folder_files),
            "file_type_count": len(extension_counts),
            "extension_counts": extension_counts,
            "input_type_count": len(resolved_extension_counts),
            "resolved_extension_counts": resolved_extension_counts,
        }

    def discover_folder_files(self, project):
        """Discovers all files in the configured input folder before extension filtering.

        Args:
            project (BatchProcessorModel): Active project model.

        Returns:
            list: Sorted normalized file paths in the source folder.
        """
        input_dir = self.get_input_dir(project)
        if not os.path.isdir(input_dir):
            return []

        include_subdirectories = bool(self.settings.get("include_subdirectories", True))
        discovered = []
        if include_subdirectories:
            walker = os.walk(input_dir)
        else:
            walker = [(input_dir, [], os.listdir(input_dir))]

        for root, _, file_names in walker:
            for file_name in file_names:
                file_path = os.path.join(root, file_name)
                if os.path.isfile(file_path):
                    discovered.append(task_base.normalize_path(file_path))
        return sorted(set(discovered))

    def prepare(self, project, context=None):
        """Builds initial work items from discovered files.

        Args:
            project (BatchProcessorModel): Active project model.
            context (dict, optional): Runtime context.

        Returns:
            list: Work items discovered by this task.
        """
        input_dir = self.get_input_dir(project)
        return [
            task_base.WorkItem(
                source_path=file_path,
                source_root=input_dir,
            )
            for file_path in self.discover_files(project)
        ]

    def _is_file_allowed(self, file_path):
        """Checks whether a file passes extension and exclude filters.

        Args:
            file_path (str): File path to evaluate.

        Returns:
            bool: True when this file should be included.
        """
        if not task_base.has_supported_extension(file_path, self.settings.get("extensions")):
            return False
        normalized_path = task_base.normalize_path(file_path).replace("\\", "/")
        file_name = os.path.basename(file_path)
        for pattern in self.settings.get("exclude_patterns") or []:
            if fnmatch.fnmatch(file_name, pattern) or fnmatch.fnmatch(normalized_path, pattern):
                return False
        return True

    def _get_explicit_path_candidates(self, explicit_entry, project):
        """Gets concrete path candidates for one explicit file entry.

        Args:
            explicit_entry (str): User-provided explicit file entry.
            project (BatchProcessorModel): Active project model.

        Returns:
            list: Path candidates to test or glob.
        """
        candidates = []

        def add_candidate(candidate):
            """Adds a candidate when it is meaningful and unique.

            Args:
                candidate (str): Candidate path.
            """
            candidate = os.path.expandvars(str(candidate or "").strip())
            if candidate and candidate not in candidates:
                candidates.append(candidate)

        add_candidate(explicit_entry)
        if project:
            add_candidate(project.resolve_template_path(explicit_entry, task=self))
        input_dir = self.get_input_dir(project) if project else ""
        if input_dir:
            template_expanded = project.resolve_template(explicit_entry, task=self) if project else explicit_entry
            template_expanded = os.path.expandvars(str(template_expanded or "").strip())
            if template_expanded and not os.path.isabs(template_expanded):
                add_candidate(os.path.join(input_dir, template_expanded))
        return candidates

    def _resolve_path_candidate(self, path_candidate):
        """Resolves a path candidate into existing file paths.

        Args:
            path_candidate (str): Path candidate or glob pattern.

        Returns:
            list: Normalized file paths.
        """
        discovered = []
        if self._has_glob_expression(path_candidate):
            matches = glob.glob(path_candidate, recursive=True)
        else:
            matches = [path_candidate]
        for file_path in matches:
            if os.path.isfile(file_path):
                discovered.append(task_base.normalize_path(file_path))
        return discovered

    def _get_explicit_match_patterns(self, explicit_entry, project):
        """Gets normalized wildcard patterns used against discovered folder files.

        Args:
            explicit_entry (str): User-provided explicit file entry.
            project (BatchProcessorModel): Active project model.

        Returns:
            list: Normalized wildcard patterns.
        """
        patterns = []

        def add_pattern(pattern):
            """Adds a normalized pattern when it is meaningful and unique.

            Args:
                pattern (str): Pattern to add.
            """
            pattern = os.path.expandvars(str(pattern or "").strip()).replace("\\", "/")
            if pattern and pattern not in patterns:
                patterns.append(pattern)

        add_pattern(explicit_entry)
        if project:
            add_pattern(project.resolve_template(explicit_entry, task=self))
            add_pattern(project.resolve_template_path(explicit_entry, task=self))
        return patterns

    def _explicit_entry_matches_file(self, file_path, patterns, input_dir="", project_dir=""):
        """Checks whether a file path matches any explicit file pattern.

        Args:
            file_path (str): File path to evaluate.
            patterns (list): Explicit file patterns.
            input_dir (str, optional): Resolved input directory.
            project_dir (str, optional): Resolved project directory.

        Returns:
            bool: True when a pattern matches the file.
        """
        normalized_path = task_base.normalize_path(file_path).replace("\\", "/")
        match_values = [normalized_path, os.path.basename(file_path)]
        for root_dir in [input_dir, project_dir]:
            if root_dir:
                try:
                    relative_path = os.path.relpath(file_path, root_dir)
                    match_values.append(relative_path.replace("\\", "/"))
                except ValueError:
                    pass
        for pattern in patterns:
            normalized_pattern = os.path.expandvars(str(pattern or "").strip()).replace("\\", "/")
            for match_value in match_values:
                if fnmatch.fnmatchcase(match_value.lower(), normalized_pattern.lower()):
                    return True
        return False

    @staticmethod
    def _has_glob_expression(path):
        """Checks whether a path contains glob wildcard characters.

        Args:
            path (str): Path or pattern to inspect.

        Returns:
            bool: True when the path contains glob wildcards.
        """
        return any(character in str(path or "") for character in ["*", "?", "["])
