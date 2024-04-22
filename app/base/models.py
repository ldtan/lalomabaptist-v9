from datetime import (
    date,
    datetime,
)
from typing import (
    List,
    Optional,
    Tuple,
)

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy_utils import (
    ScalarListType,
    URLType,
)

from ..auth.models import (
    GranularAccessMixin,
    User,
    WriterMixin,
)
from ..core.database import (
    DateTimeTrackerMixin,
    UuidMixin,
)
from ..extensions import db


class BaseModel(
    db.Model,
    UuidMixin,
    DateTimeTrackerMixin,
    WriterMixin,
    GranularAccessMixin,
):

    __abstract__ = True


class Person(BaseModel):

    __tablename__ = 'people'
    __table_args__ = (
        UniqueConstraint(
            'first_name',
            'last_name',
            'postfix',
            name='uix_full_name',
        ),
    )
    access_node_full_name = f"base.{__tablename__}"

    prefix: Mapped[Optional[str]] = mapped_column(String(10))
    first_name: Mapped[str] = mapped_column(String(255))
    middle_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255))
    postfix: Mapped[Optional[str]] = mapped_column(String(10))
    nickname: Mapped[Optional[str]] = mapped_column(String(50))
    birthday: Mapped[Optional[date]] = mapped_column(Date)
    user_id: Mapped[Optional[int]] = mapped_column(Integer,
            ForeignKey('users.id'), unique=True)

    user: Mapped[User] = relationship(foreign_keys=[user_id])

    def __repr__(self) -> str:
        return self.full_name
    
    @hybrid_property
    def full_name(self) -> str:
        full_name = self.first_name

        if self.prefix:
            full_name = self.prefix + ' ' + full_name

        if self.middle_name:
            full_name = full_name + ' ' + self.middle_name
        
        full_name = full_name + ' ' + self.last_name

        if self.postfix:
            full_name = full_name + ' ' + self.postfix

        return full_name
    
    @hybrid_property
    def age(self) -> Optional[int]:
        if self.birthday is None:
            return None
        
        birthdate = self.birthday
        today = datetime.utcnow().date()
        age = today.year - birthdate.year - ((today.month, today.day)
                < (birthdate.month, birthdate.day))

        return age


class SitePage(BaseModel):

    __tablename__ = 'pages'
    access_node_full_name = f"base.{__tablename__}"

    url_title: Mapped[str] = mapped_column(String(255), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    template_name: Mapped[Optional[str]] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return self.url_title


class Ministry(BaseModel):

    __tablename__ = 'ministries'
    access_node_full_name = f"base.{__tablename__}"

    name: Mapped[str] = mapped_column(String(255), unique=True)
    short_description: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    logo_url: Mapped[str] = mapped_column(URLType)

    def __repr__(self) -> str:
        return self.name


class Preaching(BaseModel):

    __tablename__ = 'preachings'
    access_node_full_name = f"base.{__tablename__}"

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    start_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    video_url: Mapped[Optional[str]] = mapped_column(URLType)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(URLType)
    preacher_id: Mapped[Optional[int]] = mapped_column(Integer, 
            ForeignKey('people.id'))
    
    preacher: Mapped[Optional[Person]] = relationship(
            foreign_keys=[preacher_id])

    def __repr__(self) -> str:
        return self.title
    

class Event(BaseModel):

    __tablename__ = 'events'
    access_node_full_name = f"base.{__tablename__}"

    REPEAT_CHOICES: Tuple[Tuple[str, str]] = (
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    )
    REPEAT_ON_CHOICES: Tuple[Tuple[str, str]] = (
        ('sun', 'Sunday'),
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
    )

    name: Mapped[str] = mapped_column(String(255))
    short_description: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    venue: Mapped[Optional[str]] = mapped_column(String(255))
    start_datetime: Mapped[datetime] = mapped_column(DateTime)
    end_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    repeat: Mapped[Optional[List[str]]] = mapped_column(String(255))
    repeat_on: Mapped[Optional[List[str]]] = mapped_column(ScalarListType(str))
    include_time: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return self.name
    

class BulletinPost(BaseModel):

    __tablename__ = 'bulletin_posts'
    access_node_full_name = f"base.{__tablename__}"

    IMAGE_POSITION_CHOICES: Tuple[Tuple[str, str]] = (
        ('top', 'Top'),
        ('bottom', 'Bottom'),
        ('overlay', 'Overlay'),
    )
    DISPLAY_CHOICES: Tuple[Tuple[str, str]] = (
        ('content', 'Content'),
        ('title', 'Title'),
        ('image', 'Image'),
    )

    title: Mapped[Optional[str]] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(String(255))
    image_url: Mapped[Optional[str]] = mapped_column(URLType)
    image_position: Mapped[Optional[str]] = mapped_column(String(255))
    display: Mapped[List[str]] = mapped_column(ScalarListType(str))
    pinned_until: Mapped[Optional[datetime]] = mapped_column(DateTime)
