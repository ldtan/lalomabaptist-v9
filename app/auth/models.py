from datetime import datetime
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)
from uuid import uuid4

from flask_security import (
    AsaList,
    RoleMixin,
    UserMixin,
    current_user,
    hash_password,
)
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.exc import (
    NoResultFound,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import (
    Mapped,
    Query,
    mapped_column,
    relationship,
    validates,
)
from sqlalchemy_utils import ScalarListType

from ..core.auth import current_user_id
from ..core.database import (
    DateTimeTrackerMixin,
    UuidMixin,
)
from ..extensions import db
from .constants import (
    Permission,
    ANONYMOUS,
    AUTHENTICATED,
    CONTRIBUTOR,
    SUPER_USER,
)


class UsersOnGroups(db.Model):

    __tablename__ = 'users_on_groups'
    __table_args__ = (
        UniqueConstraint(
            'user_id',
            'group_id',
            name='uix_user_group',
        ),
    )

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey('groups.id'))


class AuthModel(db.Model, UuidMixin, DateTimeTrackerMixin):

    __abstract__ = True


class AccessNode(AuthModel):

    __tablename__ = 'access_nodes'
    __table_args__ = (
        UniqueConstraint(
            'name',
            'parent_id',
            name='uix_full_name',
        ),
    )
    access_node_full_name: str = f"auth.{__tablename__}"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    parent_id: Mapped[Optional[int]] = mapped_column(Integer,
            ForeignKey('access_nodes.id'))

    children: Mapped[List['AccessNode']] = relationship('AccessNode',
            back_populates='parent')
    parent: Mapped[Optional['AccessNode']] = relationship(
            'AccessNode', back_populates='children', remote_side=[id])
    user_accesses: Mapped[List['UserAccess']] = relationship(
            back_populates='access', cascade='all, delete')
    group_accesses: Mapped[List['GroupAccess']] = relationship(
            back_populates='access', cascade='all, delete')
    
    @classmethod
    def create_by_full_name(cls, full_name: str,
            user_accesses: Optional[List['UserAccess']] = None,
            group_accesses: Optional[List['GroupAccess']] = None
        ) -> 'AccessNode':
        
        names = full_name.split('.')
        parent = None
        
        if len(names) > 1:
            parent_full_name = '.'.join(names[:-1])

            if not (parent := cls.get_by_full_name(parent_full_name)):
                raise NoResultFound(f"Parent `{parent_full_name}`" \
                        + " is not found")
            
        access_node = cls(name=names[-1], parent=parent)
        
        if user_accesses:
            db.session.add_all([
                UserAccess(
                    access=access_node,
                    user=access.user,
                    role=access.role,
                )
                for access in user_accesses
            ])

        if group_accesses:
            db.session.add_all([
                GroupAccess(
                    access=access_node,
                    group=access.group,
                    role=access.role,
                )
                for access in group_accesses
            ])
        
        db.session.add(access_node)

        return access_node
    
    @classmethod
    def get_by_full_name(cls, full_name: str) -> Optional['AccessNode']:
        names = full_name.split('.')
        parent = None
        
        for name in names:
            if (access_node := cls.query.filter_by(
                    name=name, parent=parent).first()):
                parent = access_node
            else:
                return None
            
        return access_node
    
    @classmethod
    def get_model_access_node(cls) -> Optional['AccessNode']:
        return cls.get_by_full_name(cls.access_node_full_name) \
                if cls.access_node_full_name else None
    
    def __repr__(self) -> str:
        return self.full_name
    
    @hybrid_property
    def full_name(self) -> str:
        access_node = self
        full_name = self.name
        
        while (parent := access_node.parent):
            full_name = parent.name + '.' + full_name
            access_node = parent

        return full_name
    
    @full_name.expression
    def full_name(self):
        access_node = self
        full_name = self.name
        
        while (parent := access_node.parent):
            full_name = parent.name + '.' + full_name
            access_node = parent

        return full_name
        
    def has_user_permissions(self, user: 'User',
            *permissions: List[Union[str, Permission]],
            require_all: bool = False) -> bool:
        
        if not (user and user.is_authenticated):
            return self.has_group_permissions(
                    Group.get_by_name(ANONYMOUS),
                    *permissions, require_all=require_all)
        
        if getattr(user, 'is_super_user', False):
            return True

        cls = self.__class__
        
        valid_role_ids = [role.id for role in Role.query.all() \
                if role.has_permissions(*permissions, require_all=require_all)]
        
        if not valid_role_ids:
            return False
        
        query = cls.query.join(UserAccess, cls.user_accesses, isouter=True)\
                .join(GroupAccess, cls.group_accesses, isouter=True)\
        
        user_filter = (UserAccess.user_id == user.id) \
                & UserAccess.role_id.in_(valid_role_ids)
        
        authenticated_group = Group.get_by_name(AUTHENTICATED)
        group_filter = (GroupAccess.group.has(Group.users.any(id=user.id)) \
                | (GroupAccess.group_id == authenticated_group.id)) \
                & GroupAccess.role_id.in_(valid_role_ids)
        
        query = query.filter((UserAccess.access_id == self.id) \
                & (UserAccess.access_id == self.id) 
                & (user_filter | group_filter))

        return query.count() > 0

    def has_group_permissions(self, group: 'Group',
            *permissions: List[Union[str, Permission]],
            require_all: bool = False) -> bool:
        
        cls = self.__class__
        
        valid_role_ids = [role.id for role in Role.query.all() \
                if role.has_permissions(*permissions, require_all)]
        
        if not valid_role_ids:
            return False
        
        query = cls.query.join(UserAccess, cls.user_accesses, isouter=True)\
                .join(GroupAccess, cls.group_accesses, isouter=True)
        
        query = query.filter((GroupAccess.access_id == self.id) \
                & (GroupAccess.group_id == group.id) \
                & GroupAccess.role_id.in_(valid_role_ids))

        return query.count() > 0

    def has_permissions(self,
            identity: Union['User', 'Group'],
            *permissions: List[Union[str, Permission]],
            require_all: bool = False) -> bool:
        
        if isinstance(identity, User):
            return self.has_user_permissions(identity, *permissions,
                    require_all=require_all)
        elif isinstance(identity, Group):
            return self.has_group_permissions(identity, *permissions,
                    require_all=require_all)
        else:
            raise ValueError(f"Cannot identify access with {identity}")
        

class GranularAccessMixin:

    access_node_full_name: Optional[str] = None

    @declared_attr
    def access_node_id(cls) -> Mapped[int]:
        return mapped_column(Integer, ForeignKey('access_nodes.id'),
                default=cls._access_node_id)
    
    @declared_attr
    def access_node(cls) -> Mapped[AccessNode]:
        return relationship('AccessNode', foreign_keys=[cls.access_node_id])
    
    @classmethod
    def _access_node_id(cls) -> Optional[int]:
        if cls.access_node_full_name is None:
            return None
        
        return access_node.id if (access_node :=
                AccessNode.get_by_full_name(cls.access_node_full_name)) \
                else None
    
    @classmethod
    def get_model_access_node(cls) -> Optional['AccessNode']:
        return AccessNode.get_by_full_name(cls.access_node_full_name) \
                if cls.access_node_full_name else None
            
    @classmethod
    def authorized_query(cls, *permissions: List[Union[str, Permission]],
            require_all: bool = False,
            user: Union[UserMixin, 'User'] = current_user) -> Query:
        
        query = cls.query.join(AccessNode, cls.access_node)\
                .join(UserAccess, AccessNode.user_accesses, isouter=True)\
                .join(GroupAccess, AccessNode.group_accesses, isouter=True)
        
        permissions = permissions if permissions else [Permission.READ_RECORD]
        valid_role_ids = [role.id for role in Role.query.all() \
                if role.has_permissions(*permissions, require_all=require_all)]
        
        if not valid_role_ids:
            return cls.query.filter((cls.id == 0) & (cls.id != 0))
        
        if not (user and user.is_authenticated):
            anonymous_group = Group.get_by_name(ANONYMOUS)

            return query.filter((GroupAccess.group_id == anonymous_group.id) \
                & GroupAccess.role_id.in_(valid_role_ids))
        
        if hasattr(user, 'is_super_user') and user.is_super_user:
            return cls.query
        
        user_filter = (UserAccess.user_id == user.id) \
                & UserAccess.role_id.in_(valid_role_ids)
        
        authenticated_group = Group.get_by_name(AUTHENTICATED)
        group_filter = (GroupAccess.group.has(Group.users.any(User.id == user.id)) \
                | (GroupAccess.group_id == authenticated_group.id)) \
                & GroupAccess.role_id.in_(valid_role_ids)
        
        return query.filter(user_filter | group_filter)
    
    @hybrid_property
    def has_unique_access(self):
        return self.access_node.name == str(self.uuid)


class Role(AuthModel, RoleMixin, GranularAccessMixin):

    __tablename__ = 'roles'
    access_node_full_name = f"auth.{__tablename__}"

    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    permissions: Mapped[List[str]] = mapped_column(
            MutableList.as_mutable(AsaList()), default=[])

    user_accesses: Mapped[List['UserAccess']] = relationship(
            back_populates='role')
    group_accesses: Mapped[List['GroupAccess']] = relationship(
            back_populates='role')

    @classmethod
    def get_by_name(cls, name: str) -> Optional['Role']:
        return cls.query.filter_by(name=name).first()

    def __repr__(self) -> str:
        return self.name
    
    @validates('permissions')
    def validate_permissions(self, key: str,
            value: List[Union[str, Permission]]) -> List[str]:
        
        permissions = [perm.name if isinstance(perm, Permission) else perm
                for perm in value]
        valid_permissions = Permission.names()

        for perm in permissions:
            if perm not in valid_permissions:
                raise ValueError(f"`{perm}` is not a valid permission")
            
        return permissions
    
    def has_permissions(self,
            *permissions: List[Union[str, Permission]],
            require_all: bool = False) -> bool:

        valid_permissions = Permission.names()
        permissions = [perm.name if isinstance(perm, Permission) else perm
                for perm in permissions]
        
        for perm in permissions:
            if perm not in valid_permissions:
                raise ValueError(f"`{perm}` is not a valid permission")
        
        return (all if require_all else any)\
                (perm in self.permissions for perm in permissions)


class User(AuthModel, UserMixin, GranularAccessMixin):

    __tablename__ = 'users'
    access_node_full_name = f"auth.{__tablename__}"

    username: Mapped[str] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    current_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(255))
    current_login_ip: Mapped[Optional[str]] = mapped_column(String(255))
    login_count: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    fs_uniquifier: Mapped[str] = mapped_column(String(255), unique=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    groups: Mapped[List['Group']] = relationship(secondary='users_on_groups',
            back_populates='users')
    accesses: Mapped[List['UserAccess']] = relationship(back_populates='user',
            cascade='all, delete')
    
    @classmethod
    def create_instance(cls, **kwargs: Dict[str, Any]) -> 'User':
        if (password := kwargs.get('password', None)) is None \
                or len(password) == 0:
            raise ValueError('Password cannot be null')
        else:
            kwargs['password'] = hash_password(password)
            
        if kwargs.get('uuid', None) is None:
            kwargs['uuid'] = uuid4()
        
        if kwargs.get('active', False):
            kwargs['confirmed_at'] = datetime.utcnow()

        if kwargs.get('fs_uniquifier', None) is None:
            kwargs['fs_uniquifier'] = uuid4().hex

        user = User(**kwargs)
        user_access = AccessNode.create_by_full_name(
                f"{cls.access_node_full_name}.{kwargs['uuid']}")
        user.access_node = user_access

        contributor = Role.get_by_name(CONTRIBUTOR)
        user_access = UserAccess(access=user_access,
                role=contributor, user=user)

        db.session.add(user)
        db.session.add(user_access)

        return user
    
    def __repr__(self) -> str:
        return self.username + (f"<{self.email}>" if self.email else '')
    
    @property
    def is_super_user(self) -> bool:
        auth_access = AccessNode.get_by_full_name('auth')
        super_user = Role.get_by_name(SUPER_USER)
        user_id = current_user_id()

        if auth_access and super_user and current_user and user_id:
            return UserAccess.query.filter_by(access_id=auth_access.id,
                    role_id=super_user.id,user_id=user_id).count() > 0
        else:
            return False
    

class WriterMixin:

    @declared_attr
    def created_by_id(cls) -> Mapped[Optional[int]]:
        return mapped_column(
            Integer,
            ForeignKey('users.id'),
            nullable=True,
            default=current_user_id
        )
    
    @declared_attr
    def updated_by_id(cls) -> Mapped[Optional[int]]:
        return mapped_column(
            Integer,
            ForeignKey('users.id'),
            nullable=True,
            default=current_user_id,
            onupdate=current_user_id
        )
    
    @declared_attr
    def created_by(cls) -> Mapped[Optional[User]]:
        return relationship('User', foreign_keys=[cls.created_by_id])
    
    @declared_attr
    def updated_by(cls) -> Mapped[Optional[User]]:
        return relationship('User', foreign_keys=[cls.updated_by_id])
    

class Group(AuthModel, GranularAccessMixin):

    __tablename__ = 'groups'
    access_node_full_name = f"auth.{__tablename__}"

    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    users: Mapped[List[User]] = relationship(secondary='users_on_groups',
            back_populates='groups')
    accesses: Mapped[List['GroupAccess']] = relationship(back_populates='group',
            cascade='all, delete')

    @classmethod
    def get_by_name(cls, name: str) -> Optional['Group']:
        return cls.query.filter_by(name=name).first()
    
    def __repr__(self) -> str:
        return self.name
    

class UserAccess(AuthModel):

    __tablename__ = 'user_accesses'
    __table_args__ = (
        UniqueConstraint(
            'access_id',
            'user_id',
            'role_id',
            name='uix_user_access_role',
        ),
    )
    access_node_full_name = f"auth.{__tablename__}"

    access_id: Mapped[int] = mapped_column(Integer,
            ForeignKey('access_nodes.id'))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey('roles.id'))

    access: Mapped[AccessNode] = relationship(back_populates='user_accesses')
    user: Mapped[User] = relationship(back_populates='accesses')
    role: Mapped[Role] = relationship(back_populates='user_accesses')

    def __repr__(self) -> str:
        return self.access + ': ' + self.user + ' => ' + self.role
    

class GroupAccess(AuthModel):

    __tablename__ = 'group_accesses'
    __table_args__ = (
        UniqueConstraint(
            'access_id',
            'group_id',
            'role_id',
            name='uix_group_access_role',
        ),
    )
    access_node_full_name = f"auth.{__tablename__}"

    access_id: Mapped[int] = mapped_column(Integer,
            ForeignKey('access_nodes.id'))
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey('groups.id'))
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey('roles.id'))

    access: Mapped[AccessNode] = relationship(back_populates='group_accesses')
    group: Mapped[Group] = relationship(back_populates='accesses')
    role: Mapped[Role] = relationship(back_populates='group_accesses')

    def __repr__(self) -> str:
        return self.access + ': ' + self.group + ' => ' + self.role
