import casbin
from pathlib import Path


class CasbinEnforcer:
    """Casbin RBAC Enforcer

    Single Responsibility: Authorization enforcement using RBAC.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize Casbin enforcer"""
        base_path = Path(__file__).parent
        model_path = str(base_path / "casbin_model.conf")
        policy_path = str(base_path / "casbin_policy.csv")

        self.enforcer = casbin.Enforcer(model_path, policy_path)

    def enforce(self, subject: str, object: str, action: str) -> bool:
        """Check if subject can perform action on object"""
        return self.enforcer.enforce(subject, object, action)

    def add_role_for_user(self, user: str, role: str) -> bool:
        """Add role to user"""
        return self.enforcer.add_role_for_user(user, role)

    def delete_role_for_user(self, user: str, role: str) -> bool:
        """Remove role from user"""
        return self.enforcer.delete_role_for_user(user, role)

    def get_roles_for_user(self, user: str) -> list:
        """Get all roles for user"""
        return self.enforcer.get_roles_for_user(user)

    def add_policy(self, role: str, object: str, action: str) -> bool:
        """Add policy for role"""
        return self.enforcer.add_policy(role, object, action)


# Singleton instance
casbin_enforcer = CasbinEnforcer()
