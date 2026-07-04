"""
Module Configuration
Job seeker automation sidebar modules
"""
from typing import List, Dict, Any

MENU_SECTIONS = [
    {'name': 'job_seeker', 'display_name': 'Job Seeker', 'sort_order': 0},
    {'name': 'management', 'display_name': 'Management', 'sort_order': 1},
    {'name': 'account', 'display_name': 'Account', 'sort_order': 2},
]

MODULES = [
    {
        'name': 'overview',
        'display_name': 'Overview',
        'description': 'Job search dashboard',
        'icon': 'dashboard',
        'color': 'gray',
        'permission': None,
        'blueprint_name': 'main',
        'route': 'index',
        'sort_order': 0,
        'section': 'job_seeker',
        'parent': None,
        'children': []
    },
    {
        'name': 'resume',
        'display_name': 'Resume',
        'description': 'Master profile and ATS export',
        'icon': 'resume',
        'color': 'info',
        'permission': None,
        'blueprint_name': 'resume',
        'route': 'profiles_list',
        'sort_order': 10,
        'section': 'job_seeker',
        'parent': None,
        'children': [
            {'name': 'profiles', 'display_name': 'Master Profile', 'route': 'profiles_list', 'icon': 'profile'},
            {'name': 'manual', 'display_name': 'Create Profile', 'route': 'profile_manual', 'icon': 'add'},
            {'name': 'upload', 'display_name': 'Upload Resume', 'route': 'upload', 'icon': 'upload'},
        ]
    },
    {
        'name': 'jobs',
        'display_name': 'Jobs',
        'description': 'Job postings and keyword analysis',
        'icon': 'briefcase',
        'color': 'purple',
        'permission': None,
        'blueprint_name': 'jobs',
        'route': 'postings_list',
        'sort_order': 20,
        'section': 'job_seeker',
        'parent': None,
        'children': [
            {'name': 'postings', 'display_name': 'Job Postings', 'route': 'postings_list', 'icon': 'list'},
            {'name': 'new', 'display_name': 'Add Job', 'route': 'posting_new', 'icon': 'add'},
            {'name': 'fetch', 'display_name': 'Fetch from URL', 'route': 'posting_fetch', 'icon': 'link'},
            {'name': 'discover', 'display_name': 'Discover Jobs', 'route': 'discover', 'icon': 'search'},
            {'name': 'search_profiles', 'display_name': 'Search Profiles', 'route': 'search_profiles_list', 'icon': 'filter'},
            {'name': 'inbox', 'display_name': 'Discovery Inbox', 'route': 'discovery_inbox', 'icon': 'inbox'},
        ]
    },
    {
        'name': 'applications',
        'display_name': 'Applications',
        'description': 'Track and manage applications',
        'icon': 'applications',
        'color': 'success',
        'permission': None,
        'blueprint_name': 'applications',
        'route': 'dashboard',
        'sort_order': 30,
        'section': 'job_seeker',
        'parent': None,
        'children': [
            {'name': 'list', 'display_name': 'All Applications', 'route': 'list_view', 'icon': 'list'},
            {'name': 'pipeline', 'display_name': 'Pipeline', 'route': 'pipeline', 'icon': 'kanban'},
            {'name': 'queue', 'display_name': 'Apply Queue', 'route': 'apply_queue', 'icon': 'queue'},
            {'name': 'batches', 'display_name': 'Apply Batches', 'route': 'batches_list', 'icon': 'batch'},
            {'name': 'new', 'display_name': 'New Application', 'route': 'new_application', 'icon': 'add'},
        ]
    },
    {
        'name': 'analytics',
        'display_name': 'Analytics',
        'description': 'Pipeline metrics and source effectiveness',
        'icon': 'chart',
        'color': 'info',
        'permission': None,
        'blueprint_name': 'analytics',
        'route': 'dashboard',
        'sort_order': 35,
        'section': 'job_seeker',
        'parent': None,
        'children': []
    },
    {
        'name': 'admin',
        'display_name': 'Admin',
        'description': 'System administration',
        'icon': 'settings',
        'color': 'danger',
        'permission': 'admin.access',
        'blueprint_name': 'admin',
        'route': 'dashboard',
        'sort_order': 40,
        'section': 'management',
        'parent': None,
        'children': [
            {'name': 'dashboard', 'display_name': 'Dashboard', 'route': 'dashboard', 'icon': 'chart'},
        ]
    },
    {
        'name': 'profile',
        'display_name': 'Profile',
        'description': 'Your account',
        'icon': 'user',
        'color': 'purple',
        'permission': None,
        'blueprint_name': 'users',
        'route': 'profile',
        'sort_order': 50,
        'section': 'account',
        'parent': None,
        'children': []
    },
    {
        'name': 'logout',
        'display_name': 'Logout',
        'description': 'Log out',
        'icon': 'logout',
        'color': 'gray',
        'permission': None,
        'blueprint_name': 'auth',
        'route': 'logout',
        'sort_order': 100,
        'section': 'account',
        'parent': None,
        'children': []
    },
]

ICONS = {
    # Top-level modules
    'dashboard': 'tabler-layout-dashboard',
    'resume': 'tabler-file-cv',
    'briefcase': 'tabler-briefcase',
    'applications': 'tabler-clipboard-list',
    'settings': 'tabler-settings',
    'user': 'tabler-user',
    'logout': 'tabler-logout',
    # Submenu items
    'profile': 'tabler-user-circle',
    'upload': 'tabler-upload',
    'list': 'tabler-list',
    'add': 'tabler-plus',
    'link': 'tabler-link',
    'search': 'tabler-search',
    'kanban': 'tabler-layout-kanban',
    'chart': 'tabler-chart-bar',
    'filter': 'tabler-filter',
    'inbox': 'tabler-inbox',
    'queue': 'tabler-list-check',
    'batch': 'tabler-stack-2',
}

COLOR_CLASSES = {
    'purple': {
        'bg': 'bg-purple-100 dark:bg-purple-900',
        'hover': 'group-hover:bg-purple-200 dark:group-hover:bg-purple-800',
        'text': 'text-purple-600 dark:text-purple-400'
    },
    'gray': {
        'bg': 'bg-gray-100 dark:bg-gray-700',
        'hover': 'group-hover:bg-gray-200 dark:group-hover:bg-gray-600',
        'text': 'text-gray-600 dark:text-gray-400'
    },
    'info': {
        'bg': 'bg-blue-100 dark:bg-blue-900',
        'hover': 'group-hover:bg-blue-200 dark:group-hover:bg-blue-800',
        'text': 'text-blue-600 dark:text-blue-400'
    },
    'success': {
        'bg': 'bg-green-100 dark:bg-green-900',
        'hover': 'group-hover:bg-green-200 dark:group-hover:bg-green-800',
        'text': 'text-green-600 dark:text-green-400'
    },
    'danger': {
        'bg': 'bg-red-100 dark:bg-red-900',
        'hover': 'group-hover:bg-red-200 dark:group-hover:bg-red-800',
        'text': 'text-red-600 dark:text-red-400'
    },
}


def get_visible_modules(user) -> List[Dict[str, Any]]:
    visible_modules = []
    for module in MODULES:
        if module['name'] == 'overview':
            visible_modules.append(module)
        elif module.get('permission'):
            if module['permission'] == 'admin.access':
                if hasattr(user, 'is_admin') and hasattr(user, 'is_superadmin'):
                    if user.is_admin or user.is_superadmin:
                        visible_modules.append(module)
            elif hasattr(user, 'has_permission') and user.has_permission(module['permission']):
                visible_modules.append(module)
        else:
            visible_modules.append(module)
    visible_modules.sort(key=lambda x: x['sort_order'])
    return visible_modules


def get_modules_by_section(user) -> Dict[str, List[Dict[str, Any]]]:
    visible_modules = get_visible_modules(user)
    modules_by_section = {}
    for section in MENU_SECTIONS:
        modules_by_section[section['name']] = [
            m for m in visible_modules if m.get('section') == section['name']
        ]
    return modules_by_section
