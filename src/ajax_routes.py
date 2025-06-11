"""
AJAX routes for ProjectCatalog.

This module provides AJAX endpoints for loading data asynchronously,
improving UI responsiveness and user experience.
"""

from bottle import route, response, request
import json
import time
from datetime import datetime

from src.config import SOURCE_DIRS
from src.activity_tracker import get_recent_activity
from src.deferred_startup import startup_manager


@route('/api/startup_status')
def get_startup_status():
    """Get the current startup status of background services."""
    response.content_type = 'application/json'
    response.headers['Cache-Control'] = 'no-cache'
    
    status = startup_manager.get_startup_status()
    
    return json.dumps({
        'background_threads_started': status['background_threads_started'],
        'startup_complete': status['startup_complete'],
        'timestamp': time.time()
    })


@route('/api/activity_data')
def get_activity_data_ajax():
    """Get activity data via AJAX for asynchronous loading."""
    response.content_type = 'application/json'
    response.headers['Cache-Control'] = 'no-cache'
    
    try:
        # Get parameters
        force_refresh = request.query.get('refresh', 'false').lower() == 'true'
        directories_param = request.query.get('directories', '')
        
        # Determine which directories to scan
        if directories_param:
            # If specific directories are requested
            directories_to_scan = [d.strip() for d in directories_param.split(',') if d.strip()]
        else:
            # Default to all source directories
            directories_to_scan = SOURCE_DIRS
        
        print(f"AJAX: Getting activity data for {len(directories_to_scan)} directories, force_refresh={force_refresh}")
        
        # Get activity data
        activity_data = get_recent_activity(directories_to_scan, force_refresh=force_refresh)
        
        # Format the response
        projects_with_activity = []
        
        for dir_path, dir_info in activity_data.items():
            # Skip if no projects or directory info is incomplete
            if 'projects' not in dir_info:
                continue
            
            # Process each project in this directory
            for project in dir_info.get('projects', []):
                # Skip projects without valid last_modified data
                if 'last_modified' not in project:
                    continue
                
                projects_with_activity.append({
                    'path': project['path'],
                    'name': project.get('name', project['path'].split('/')[-1]),
                    'source_dir': dir_path,
                    'last_modified': project['last_modified'],
                    'last_modified_str': datetime.fromtimestamp(project['last_modified']).strftime('%Y-%m-%d %H:%M'),
                    'recent_files': project.get('recent_files', []),
                    'days_since_modified': project.get('days_since_modified', 0)
                })
        
        # Sort by last modified time (most recent first)
        projects_with_activity.sort(key=lambda x: x['last_modified'], reverse=True)
        
        return json.dumps({
            'success': True,
            'projects': projects_with_activity,
            'total_directories': len(directories_to_scan),
            'processed_directories': len(activity_data),
            'total_projects': len(projects_with_activity),
            'force_refresh': force_refresh,
            'timestamp': time.time()
        })
        
    except Exception as e:
        print(f"Error in get_activity_data_ajax: {str(e)}")
        return json.dumps({
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        })


@route('/api/project_list')
def get_project_list_ajax():
    """Get project list via AJAX for asynchronous loading."""
    response.content_type = 'application/json'
    response.headers['Cache-Control'] = 'no-cache'
    
    try:
        import os
        from pathlib import Path
        from src.project_analyzer import get_project_info
        from src.projectcatalog import analysis_queue
        
        # Get parameters
        directory = request.query.get('directory', '')
        show_all = request.query.get('show_all', 'false').lower() == 'true'
        force_refresh_activity = request.query.get('refresh', 'false').lower() == 'true'
        
        projects = []
        
        if show_all:
            # Get projects from all directories
            directories_to_scan = SOURCE_DIRS
        else:
            # Get projects from specific directory
            if not directory or not os.path.exists(directory):
                return json.dumps({
                    'success': False,
                    'error': f'Invalid directory: {directory}',
                    'timestamp': time.time()
                })
            directories_to_scan = [directory]
        
        # Get activity data for the directories
        activity_data = get_recent_activity(directories_to_scan, force_refresh=force_refresh_activity)
        
        # Create activity lookup
        activity_lookup = {}
        for source_dir, data in activity_data.items():
            for project in data.get('projects', []):
                activity_lookup[project['path']] = {
                    'last_modified': project.get('last_modified'),
                    'last_modified_str': datetime.fromtimestamp(project.get('last_modified', 0)).strftime('%Y-%m-%d %H:%M'),
                    'recent_files': project.get('recent_files', [])
                }
        
        # Get list of projects currently in the analysis queue
        queued_projects = list(analysis_queue.queue)
        
        # Scan directories for projects
        for source_dir in directories_to_scan:
            if not os.path.exists(source_dir):
                continue
                
            try:
                with os.scandir(source_dir) as entries:
                    for entry in entries:
                        if entry.is_dir():
                            # Get project info including tags
                            project_info = get_project_info(Path(entry.path))
                            
                            # Get activity info
                            activity_info = activity_lookup.get(entry.path, {})
                            
                            # Check if project is in analysis queue
                            in_queue = entry.path in queued_projects
                            
                            projects.append({
                                'path': entry.path,
                                'name': entry.name,
                                'source_dir': source_dir,
                                'has_readme': project_info.get('has_readme', False),
                                'readme_size': project_info.get('readme_size', 0),
                                'languages': project_info.get('languages', []),
                                'tags': project_info.get('tags', []),
                                'last_modified': activity_info.get('last_modified'),
                                'last_modified_str': activity_info.get('last_modified_str', ''),
                                'recent_files': activity_info.get('recent_files', []),
                                'in_analysis_queue': in_queue,
                                'analysis_complete': project_info.get('analysis_complete', False)
                            })
            except PermissionError as e:
                print(f"Permission error scanning {source_dir}: {e}")
            except Exception as e:
                print(f"Error scanning {source_dir}: {e}")
        
        return json.dumps({
            'success': True,
            'projects': projects,
            'total_projects': len(projects),
            'directories_scanned': len(directories_to_scan),
            'show_all': show_all,
            'directory': directory,
            'timestamp': time.time()
        })
        
    except Exception as e:
        print(f"Error in get_project_list_ajax: {str(e)}")
        return json.dumps({
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        })
