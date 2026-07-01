"""
RBAC Service
Centralized service for role and permission management
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy import and_, or_
from app.extensions.core import db
from app.models.auth import Role, User, Group
from app.models.rbac import Permission, UserRoleAssignment, RoleHierarchy
import logging

logger = logging.getLogger(__name__)


class RBACService:
    """Service for managing roles, permissions, and assignments"""
    
    # ============================================================================
    # Permission Management
    # ============================================================================
    
    @staticmethod
    def create_permission(name: str, display_name: str, module: str, 
                         description: str = None, category: str = None,
                         is_system: bool = False, priority: int = 0) -> Permission:
        """
        Create a new permission
        
        Args:
            name: Permission name (e.g., 'users.create')
            display_name: Human-readable name
            module: Module name (e.g., 'users')
            description: Permission description
            category: Permission category
            is_system: Whether this is a system permission
            priority: Display priority
        
        Returns:
            Permission: Created permission
        """
        permission = Permission(
            name=name,
            display_name=display_name,
            module=module,
            description=description,
            category=category,
            is_system=is_system,
            priority=priority
        )
        db.session.add(permission)
        db.session.commit()
        
        logger.info(f"Created permission: {name}")
        return permission
    
    @staticmethod
    def get_permission(permission_id: str = None, name: str = None) -> Optional[Permission]:
        """Get permission by ID or name"""
        if permission_id:
            return Permission.query.get(permission_id)
        elif name:
            return Permission.get_by_name(name)
        return None
    
    @staticmethod
    def get_all_permissions(active_only: bool = True) -> List[Permission]:
        """Get all permissions"""
        query = Permission.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(Permission.module, Permission.priority, Permission.name).all()
    
    @staticmethod
    def get_permissions_by_module(module: str, active_only: bool = True) -> List[Permission]:
        """Get all permissions for a specific module"""
        query = Permission.query.filter_by(module=module)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(Permission.priority, Permission.name).all()
    
    @staticmethod
    def get_permissions_grouped_by_module(active_only: bool = True) -> Dict[str, List[Permission]]:
        """Get permissions grouped by module"""
        permissions = RBACService.get_all_permissions(active_only)
        grouped = {}
        for perm in permissions:
            if perm.module not in grouped:
                grouped[perm.module] = []
            grouped[perm.module].append(perm)
        return grouped
    
    @staticmethod
    def update_permission(permission_id: str, **kwargs) -> Permission:
        """Update permission attributes"""
        permission = Permission.query.get(permission_id)
        if not permission:
            raise ValueError(f"Permission {permission_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(permission, key):
                setattr(permission, key, value)
        
        permission.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Updated permission: {permission.name}")
        return permission
    
    @staticmethod
    def delete_permission(permission_id: str, force: bool = False) -> bool:
        """
        Delete a permission
        
        Args:
            permission_id: Permission ID
            force: If True, delete even if it's a system permission
        
        Returns:
            bool: True if deleted
        """
        permission = Permission.query.get(permission_id)
        if not permission:
            return False
        
        if permission.is_system and not force:
            raise ValueError("Cannot delete system permission without force=True")
        
        db.session.delete(permission)
        db.session.commit()
        
        logger.info(f"Deleted permission: {permission.name}")
        return True
    
    # ============================================================================
    # Role Management
    # ============================================================================
    
    @staticmethod
    def create_role(name: str, display_name: str = None, description: str = None,
                   is_system_role: bool = False, priority: int = 0) -> Role:
        """Create a new role"""
        role = Role(
            name=name,
            display_name=display_name or name,
            description=description,
            is_system_role=is_system_role,
            priority=priority
        )
        db.session.add(role)
        db.session.commit()
        
        logger.info(f"Created role: {name}")
        return role
    
    @staticmethod
    def get_role(role_id: str = None, name: str = None) -> Optional[Role]:
        """Get role by ID or name"""
        if role_id:
            return Role.query.get(role_id)
        elif name:
            return Role.query.filter_by(name=name).first()
        return None
    
    @staticmethod
    def get_all_roles(active_only: bool = True) -> List[Role]:
        """Get all roles"""
        query = Role.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(Role.priority.desc(), Role.name).all()
    
    @staticmethod
    def update_role(role_id: str, **kwargs) -> Role:
        """Update role attributes"""
        role = Role.query.get(role_id)
        if not role:
            raise ValueError(f"Role {role_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(role, key):
                setattr(role, key, value)
        
        role.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Updated role: {role.name}")
        return role
    
    @staticmethod
    def delete_role(role_id: str, force: bool = False) -> bool:
        """Delete a role"""
        role = Role.query.get(role_id)
        if not role:
            return False
        
        if role.is_system_role and not force:
            raise ValueError("Cannot delete system role without force=True")
        
        db.session.delete(role)
        db.session.commit()
        
        logger.info(f"Deleted role: {role.name}")
        return True
    
    # ============================================================================
    # Role-Permission Management
    # ============================================================================
    
    @staticmethod
    def assign_permission_to_role(role_id: str, permission_id: str) -> bool:
        """Assign a permission to a role"""
        role = Role.query.get(role_id)
        permission = Permission.query.get(permission_id)
        
        if not role or not permission:
            return False
        
        role.add_permission(permission)
        db.session.commit()
        
        logger.info(f"Assigned permission {permission.name} to role {role.name}")
        return True
    
    @staticmethod
    def remove_permission_from_role(role_id: str, permission_id: str) -> bool:
        """Remove a permission from a role"""
        role = Role.query.get(role_id)
        permission = Permission.query.get(permission_id)
        
        if not role or not permission:
            return False
        
        role.remove_permission(permission)
        db.session.commit()
        
        logger.info(f"Removed permission {permission.name} from role {role.name}")
        return True
    
    @staticmethod
    def get_role_permissions(role_id: str) -> List[Permission]:
        """Get all permissions for a role"""
        role = Role.query.get(role_id)
        if not role:
            return []
        
        return role.permission_list.filter_by(is_active=True).all()
    
    @staticmethod
    def sync_role_permissions(role_id: str, permission_ids: List[str]) -> bool:
        """
        Sync role permissions (replace all with new list)
        
        Args:
            role_id: Role ID
            permission_ids: List of permission IDs to assign
        
        Returns:
            bool: True if successful
        """
        role = Role.query.get(role_id)
        if not role:
            return False
        
        # Get all permissions
        permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
        
        # Clear existing permissions
        role.permission_list.delete()
        
        # Add new permissions
        for permission in permissions:
            role.add_permission(permission)
        
        db.session.commit()
        
        logger.info(f"Synced {len(permissions)} permissions to role {role.name}")
        return True
    
    # ============================================================================
    # User-Role Assignment
    # ============================================================================
    
    @staticmethod
    def assign_role_to_user(user_id: str, role_id: str, assigned_by_id: str = None,
                           expires_at: datetime = None, notes: str = None) -> UserRoleAssignment:
        """
        Assign a role to a user
        
        Args:
            user_id: User ID
            role_id: Role ID
            assigned_by_id: ID of user making the assignment
            expires_at: Optional expiration date
            notes: Optional notes
        
        Returns:
            UserRoleAssignment: Created assignment
        """
        # Check if assignment already exists
        existing = UserRoleAssignment.query.filter_by(
            user_id=user_id,
            role_id=role_id
        ).first()
        
        if existing:
            if existing.is_active:
                raise ValueError("User already has this role")
            # Reactivate existing assignment
            existing.is_active = True
            existing.assigned_by = assigned_by_id
            existing.assigned_at = datetime.utcnow()
            existing.expires_at = expires_at
            existing.notes = notes
            existing.revoked_at = None
            existing.revoked_by = None
            existing.revoke_reason = None
            db.session.commit()
            return existing
        
        # Create new assignment
        assignment = UserRoleAssignment(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by_id,
            expires_at=expires_at,
            notes=notes
        )
        db.session.add(assignment)
        db.session.commit()
        
        logger.info(f"Assigned role {role_id} to user {user_id}")
        return assignment
    
    @staticmethod
    def revoke_role_from_user(user_id: str, role_id: str, revoked_by_id: str = None,
                              reason: str = None) -> bool:
        """Revoke a role from a user"""
        assignment = UserRoleAssignment.query.filter_by(
            user_id=user_id,
            role_id=role_id,
            is_active=True
        ).first()
        
        if not assignment:
            return False
        
        assignment.revoke(revoked_by_id, reason)
        db.session.commit()
        
        logger.info(f"Revoked role {role_id} from user {user_id}")
        return True
    
    @staticmethod
    def get_user_roles(user_id: str, active_only: bool = True) -> List[UserRoleAssignment]:
        """Get all role assignments for a user"""
        query = UserRoleAssignment.query.filter_by(user_id=user_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    @staticmethod
    def get_role_users(role_id: str, active_only: bool = True) -> List[UserRoleAssignment]:
        """Get all user assignments for a role"""
        query = UserRoleAssignment.query.filter_by(role_id=role_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()

    @staticmethod
    def get_role_assignment_counts() -> Dict[str, int]:
        """Get user assignment count per role (for list views). Returns {role_id: count}."""
        from sqlalchemy import func
        rows = db.session.query(
            UserRoleAssignment.role_id,
            func.count(UserRoleAssignment.id).label('count')
        ).group_by(UserRoleAssignment.role_id).all()
        return {str(role_id): count for role_id, count in rows}
    
    @staticmethod
    def cleanup_expired_assignments() -> int:
        """
        Clean up expired role assignments
        
        Returns:
            int: Number of assignments cleaned up
        """
        expired = UserRoleAssignment.query.filter(
            and_(
                UserRoleAssignment.is_active == True,
                UserRoleAssignment.expires_at != None,
                UserRoleAssignment.expires_at < datetime.utcnow()
            )
        ).all()
        
        count = 0
        for assignment in expired:
            assignment.is_active = False
            assignment.revoked_at = datetime.utcnow()
            assignment.revoke_reason = "Expired"
            count += 1
        
        if count > 0:
            db.session.commit()
            logger.info(f"Cleaned up {count} expired role assignments")
        
        return count
    
    # ============================================================================
    # Role Hierarchy
    # ============================================================================
    
    @staticmethod
    def create_role_hierarchy(parent_role_id: str, child_role_id: str,
                             created_by_id: str = None) -> RoleHierarchy:
        """Create a parent-child relationship between roles"""
        if parent_role_id == child_role_id:
            raise ValueError("Role cannot be its own parent")
        
        # Check if hierarchy already exists
        existing = RoleHierarchy.query.filter_by(
            parent_role_id=parent_role_id,
            child_role_id=child_role_id
        ).first()
        
        if existing:
            raise ValueError("Hierarchy already exists")
        
        hierarchy = RoleHierarchy(
            parent_role_id=parent_role_id,
            child_role_id=child_role_id,
            created_by=created_by_id
        )
        db.session.add(hierarchy)
        db.session.commit()
        
        logger.info(f"Created role hierarchy: {parent_role_id} -> {child_role_id}")
        return hierarchy
    
    @staticmethod
    def delete_role_hierarchy(parent_role_id: str, child_role_id: str) -> bool:
        """Delete a role hierarchy relationship"""
        hierarchy = RoleHierarchy.query.filter_by(
            parent_role_id=parent_role_id,
            child_role_id=child_role_id
        ).first()
        
        if not hierarchy:
            return False
        
        db.session.delete(hierarchy)
        db.session.commit()
        
        logger.info(f"Deleted role hierarchy: {parent_role_id} -> {child_role_id}")
        return True
    
    @staticmethod
    def get_role_hierarchy(role_id: str) -> Dict[str, List[Role]]:
        """
        Get role hierarchy (parents and children)
        
        Returns:
            dict: {'parents': [...], 'children': [...]}
        """
        parent_hierarchies = RoleHierarchy.get_parent_roles(role_id)
        child_hierarchies = RoleHierarchy.get_child_roles(role_id)
        
        return {
            'parents': [h.parent_role for h in parent_hierarchies],
            'children': [h.child_role for h in child_hierarchies]
        }
    
    # ============================================================================
    # Utility Methods
    # ============================================================================
    
    @staticmethod
    def check_user_permission(user_id: str, permission_name: str) -> bool:
        """Check if a user has a specific permission"""
        user = User.query.get(user_id)
        if not user:
            return False
        return user.has_permission(permission_name)
    
    @staticmethod
    def get_user_all_permissions(user_id: str) -> List[str]:
        """Get all permission names for a user"""
        user = User.query.get(user_id)
        if not user:
            return []
        return user.get_all_permissions()
    
    @staticmethod
    def get_statistics() -> Dict:
        """Get RBAC statistics. Rolls back on failure so session is not left in failed state."""
        try:
            return {
                'total_permissions': Permission.query.count(),
                'active_permissions': Permission.query.filter_by(is_active=True).count(),
                'total_roles': Role.query.count(),
                'active_roles': Role.query.filter_by(is_active=True).count(),
                'total_assignments': UserRoleAssignment.query.count(),
                'active_assignments': UserRoleAssignment.query.filter_by(is_active=True).count(),
                'expired_assignments': UserRoleAssignment.query.filter(
                    and_(
                        UserRoleAssignment.is_active == True,
                        UserRoleAssignment.expires_at != None,
                        UserRoleAssignment.expires_at < datetime.utcnow()
                    )
                ).count(),
                'role_hierarchies': RoleHierarchy.query.count()
            }
        except Exception:
            logger.exception("Error getting RBAC statistics")
            db.session.rollback()
            raise


# Global RBAC service instance
rbac_service = RBACService()
