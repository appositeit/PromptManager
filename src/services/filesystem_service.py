from loguru import logger
import os
from typing import List, Optional

# Placeholder for response model, ideally defined in a shared models area or imported
# For now, mirroring the structure expected by the API endpoint for clarity.
class FilesystemCompletionResponseData:
    def __init__(self, completed_path: str, suggestions: List[str], is_directory: bool):
        self.completed_path = completed_path
        self.suggestions = suggestions
        self.is_directory = is_directory

class FilesystemService:
    """Provides services for interacting with the filesystem, like path completion."""

    def __init__(self, allowed_base_paths: Optional[List[str]] = None):
        """
        Initializes the FilesystemService.

        Args:
            allowed_base_paths: A list of absolute base paths the service is allowed to explore.
                                If None or empty, defaults to the user's home directory and project root.
        """
        if allowed_base_paths:
            self.allowed_base_paths = [os.path.abspath(p) for p in allowed_base_paths]
        else:
            # Default to user's home directory and current working directory (project root)
            # This needs to be determined safely, e.g. from project config or environment
            # For now, using home and current dir as a placeholder.
            self.allowed_base_paths = [
                os.path.expanduser("~"),
                os.getcwd() # This would be the CWD of the server process
            ]
        logger.info(f"FilesystemService initialized. Allowed base paths: {self.allowed_base_paths}")

    def _is_path_allowed(self, path_to_check: str) -> bool:
        """Checks if the given path is within one of the allowed base paths."""
        abs_path_to_check = os.path.abspath(os.path.expanduser(path_to_check))
        for base_path in self.allowed_base_paths:
            # Check if abs_path_to_check is the base_path, a sub-path of it,
            # or an ancestor of it.
            common = os.path.commonpath([abs_path_to_check, base_path])
            if common == base_path or common == abs_path_to_check:
                return True
        logger.warning(f"Path '{path_to_check}' (resolved to '{abs_path_to_check}') is outside allowed base paths.")
        return False

    def get_path_completions(self, partial_path: str) -> FilesystemCompletionResponseData:
        """
        Provides path completion suggestions for a given partial path.
        This is a placeholder and needs a robust and secure implementation.

        Args:
            partial_path: The partial path string entered by the user.

        Returns:
            A FilesystemCompletionResponseData object.
        """
        logger.debug(f"FilesystemService: get_path_completions called for partial_path: '{partial_path}'")

        # Expand ~ if present
        expanded_partial_path = os.path.expanduser(partial_path)

        # Determine the directory to scan and the part to match
        if not expanded_partial_path or expanded_partial_path.endswith("/"):
            # User wants to list contents of a directory
            dir_to_scan = expanded_partial_path
            prefix_to_match = ""
        else:
            dir_to_scan = os.path.dirname(expanded_partial_path)
            prefix_to_match = os.path.basename(expanded_partial_path)
        
        # If dir_to_scan is empty (e.g. user types "abc"), use current dir or a sensible default.
        if not dir_to_scan:
            # This default needs to be context-aware, e.g., user's home or project root
            # For now, let's use a placeholder based on allowed paths or simply "."
            # A better approach would be to infer from allowed_base_paths
            dir_to_scan = "." # Fallback, needs refinement
            if not self._is_path_allowed(dir_to_scan):
                 # Try first allowed base path if current dir isn't good
                 if self.allowed_base_paths:
                     dir_to_scan = self.allowed_base_paths[0]
                 else:
                     logger.warning("No allowed base paths and '.' is not allowed for scanning.")
                     return FilesystemCompletionResponseData(partial_path, [], False)

        # Security Check: Ensure the directory to scan is within allowed paths
        if not self._is_path_allowed(dir_to_scan):
            logger.warning(f"Scan directory '{dir_to_scan}' is not allowed.")
            return FilesystemCompletionResponseData(partial_path, [], False)

        suggestions = []
        completed_path = partial_path # Start with what user typed
        is_directory_suggestion = False

        try:
            if not os.path.isdir(dir_to_scan):
                logger.debug(f"Path '{dir_to_scan}' to scan is not a directory.")
                return FilesystemCompletionResponseData(partial_path, [], False)

            logger.debug(f"Scanning directory: '{dir_to_scan}', matching prefix: '{prefix_to_match}'")
            for name in os.listdir(dir_to_scan):
                if name.startswith(prefix_to_match) and not name.startswith('.'): # Ignore hidden files
                    full_path_suggestion = os.path.join(dir_to_scan, name)
                    if os.path.isdir(full_path_suggestion):
                        suggestions.append(name + "/")
            
            suggestions.sort() # Sort the suggestions alphabetically
            logger.debug(f"Found raw directory suggestions: {suggestions}")

            if len(suggestions) == 1:
                # Single exact match or single completable item
                single_suggestion = suggestions[0]
                completed_path = os.path.join(os.path.dirname(expanded_partial_path) if not expanded_partial_path.endswith("/") and not prefix_to_match=="" else expanded_partial_path , single_suggestion)
                if not partial_path.startswith("/") and not completed_path.startswith(os.path.expanduser("~")):
                    # Handle relative paths better - this logic needs review
                    pass # For now, keep as is if relative
                is_directory_suggestion = completed_path.endswith("/")
                suggestions = [] # Clear suggestions, it's a direct completion
            elif len(suggestions) > 1:
                # Multiple matches, find common prefix
                # commonprefix needs them to be full paths from the typed prefix_to_match part
                common_prefix = os.path.commonprefix(suggestions) # commonprefix on just names like 'doc/', 'down/'
                
                if common_prefix and common_prefix != prefix_to_match:
                    # A real common prefix beyond what was typed exists
                    completed_path = os.path.join(os.path.dirname(expanded_partial_path) if not expanded_partial_path.endswith("/") and not prefix_to_match=="" else expanded_partial_path, common_prefix)
                    # Update suggestions to be relative to the new common_prefix
                    new_suggestions = []
                    for s in suggestions:
                        if s.startswith(common_prefix):
                            remaining_part = s[len(common_prefix):]
                            if remaining_part: # Don't add empty string if it was an exact match to prefix
                                new_suggestions.append(remaining_part)
                    # Ensure new_suggestions are also sorted if they were re-calculated
                    new_suggestions.sort()
                    suggestions = new_suggestions
                    is_directory_suggestion = True # Common prefix usually implies directory context for further tabbing
                else:
                    # No further common prefix, or common prefix is just what was typed.
                    # completed_path remains partial_path (or the dir part if user ended with /)
                    if expanded_partial_path.endswith("/"):
                        completed_path = expanded_partial_path
                    else:
                        completed_path = os.path.join(os.path.dirname(expanded_partial_path), prefix_to_match) if prefix_to_match else os.path.dirname(expanded_partial_path) + "/"
                    # Keep all original suggestions (but ensure they are just the next component)
                    # suggestions = [s[len(prefix_to_match):] for s in suggestions] # this might be wrong
                    # The suggestions should be the full names relative to dir_to_scan
                    pass # Keep suggestions as they are, full names like 'docs/', 'downloads/'

        except FileNotFoundError:
            logger.debug(f"Directory '{dir_to_scan}' not found for completion.")
            return FilesystemCompletionResponseData(partial_path, [], False)
        except PermissionError:
            logger.warning(f"Permission denied for accessing '{dir_to_scan}' for completion.")
            return FilesystemCompletionResponseData(partial_path, [], False)
        except Exception as e:
            logger.error(f"Error during path completion for '{partial_path}': {e}", exc_info=True)
            return FilesystemCompletionResponseData(partial_path, [], False)

        logger.debug(f"Returning completion: path='{completed_path}', suggestions={suggestions}, is_dir={is_directory_suggestion}")
        return FilesystemCompletionResponseData(completed_path, suggestions, is_directory_suggestion)

# Example Usage (for testing locally):
# if __name__ == '__main__':
#     # Configure logger for local testing
#     import sys
#     logger.remove()
#     logger.add(sys.stderr, level="DEBUG")
# 
#     fs_service = FilesystemService()
#     
#     test_paths = [
#         "~/Doc",
#         "~/Documents/",
#         "/us",
#         "/usr/l",
#         "/usr/local/s",
#         "nonexistentpath",
#         "",
#         "./s",
#         "src/serv"
#     ]
#     for tp in test_paths:
#         print(f"\nTesting: '{tp}'")
#         result = fs_service.get_path_completions(tp)
#         print(f"  Completed: '{result.completed_path}', Suggestions: {result.suggestions}, IsDir: {result.is_directory}") 