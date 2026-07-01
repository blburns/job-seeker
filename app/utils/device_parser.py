"""
Device and User Agent Parser
Parse user agent strings to extract device information
"""

import re


def parse_user_agent(user_agent_string):
    """
    Parse user agent string to extract browser, OS, and device information
    
    Args:
        user_agent_string: User agent string from request
    
    Returns:
        dict: {browser, os, device, device_type}
    """
    if not user_agent_string:
        return {
            'browser': 'Unknown',
            'os': 'Unknown',
            'device': 'Unknown',
            'device_type': 'unknown'
        }
    
    ua = user_agent_string.lower()
    
    # Detect browser
    browser = detect_browser(ua)
    
    # Detect OS
    os = detect_os(ua)
    
    # Detect device type
    device_type = detect_device_type(ua)
    
    # Detect device name (for mobile)
    device = detect_device(ua)
    
    return {
        'browser': browser,
        'os': os,
        'device': device,
        'device_type': device_type
    }


def detect_browser(ua):
    """Detect browser from user agent"""
    if 'edg/' in ua or 'edge/' in ua:
        return 'Edge'
    elif 'opr/' in ua or 'opera' in ua:
        return 'Opera'
    elif 'chrome' in ua and 'safari' in ua:
        return 'Chrome'
    elif 'firefox' in ua:
        return 'Firefox'
    elif 'safari' in ua:
        return 'Safari'
    elif 'msie' in ua or 'trident' in ua:
        return 'Internet Explorer'
    else:
        return 'Unknown Browser'


def detect_os(ua):
    """Detect operating system from user agent"""
    if 'windows nt 10' in ua:
        return 'Windows 10'
    elif 'windows nt 6.3' in ua:
        return 'Windows 8.1'
    elif 'windows nt 6.2' in ua:
        return 'Windows 8'
    elif 'windows nt 6.1' in ua:
        return 'Windows 7'
    elif 'windows' in ua:
        return 'Windows'
    elif 'mac os x' in ua or 'macos' in ua:
        # Extract macOS version if possible
        match = re.search(r'mac os x ([\d_]+)', ua)
        if match:
            version = match.group(1).replace('_', '.')
            return f'macOS {version}'
        return 'macOS'
    elif 'iphone' in ua:
        return 'iOS'
    elif 'ipad' in ua:
        return 'iPadOS'
    elif 'android' in ua:
        # Extract Android version if possible
        match = re.search(r'android ([\d.]+)', ua)
        if match:
            version = match.group(1)
            return f'Android {version}'
        return 'Android'
    elif 'linux' in ua:
        if 'ubuntu' in ua:
            return 'Ubuntu'
        return 'Linux'
    elif 'cros' in ua:
        return 'Chrome OS'
    else:
        return 'Unknown OS'


def detect_device_type(ua):
    """Detect device type from user agent"""
    if 'mobile' in ua or 'android' in ua and 'mobile' in ua:
        return 'mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        return 'tablet'
    else:
        return 'desktop'


def detect_device(ua):
    """Detect specific device name from user agent"""
    # iPhone models
    if 'iphone' in ua:
        if 'iphone14' in ua or 'iphone 14' in ua:
            return 'iPhone 14'
        elif 'iphone13' in ua or 'iphone 13' in ua:
            return 'iPhone 13'
        elif 'iphone12' in ua or 'iphone 12' in ua:
            return 'iPhone 12'
        elif 'iphone11' in ua or 'iphone 11' in ua:
            return 'iPhone 11'
        else:
            return 'iPhone'
    
    # iPad models
    elif 'ipad' in ua:
        if 'ipad pro' in ua:
            return 'iPad Pro'
        elif 'ipad air' in ua:
            return 'iPad Air'
        elif 'ipad mini' in ua:
            return 'iPad Mini'
        else:
            return 'iPad'
    
    # Samsung devices
    elif 'samsung' in ua or 'sm-' in ua:
        if 'galaxy s23' in ua or 'sm-s23' in ua:
            return 'Samsung Galaxy S23'
        elif 'galaxy s22' in ua or 'sm-s22' in ua:
            return 'Samsung Galaxy S22'
        elif 'galaxy s21' in ua or 'sm-s21' in ua:
            return 'Samsung Galaxy S21'
        elif 'galaxy' in ua:
            return 'Samsung Galaxy'
        else:
            return 'Samsung Device'
    
    # Google Pixel
    elif 'pixel' in ua:
        if 'pixel 7' in ua:
            return 'Google Pixel 7'
        elif 'pixel 6' in ua:
            return 'Google Pixel 6'
        else:
            return 'Google Pixel'
    
    # Generic Android
    elif 'android' in ua:
        return 'Android Device'
    
    # Desktop/Laptop (no specific device name)
    else:
        return ''


def get_device_icon(device_type):
    """Get icon class for device type"""
    icons = {
        'mobile': 'ti-device-mobile',
        'tablet': 'ti-device-tablet',
        'desktop': 'ti-device-desktop',
        'unknown': 'ti-device-unknown'
    }
    return icons.get(device_type, 'ti-device-unknown')
