from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ProjectCategory(str, Enum):
    CREATIVE = "creative"
    SOCIAL = "social"
    TECH = "tech"
    CHARITY = "charity"


class FundingModel(str, Enum):
    ALL_OR_NOTHING = "all_or_nothing"
    FLEXIBLE = "flexible"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    MODERATION = "moderation"
    ACTIVE = "active"
    ENDED = "ended"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModerationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PaymentMethod(str, Enum):
    CARD = "card"
    YOOMONEY = "yoomoney"
    EWALLET = "ewallet"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    REFUNDED = "refunded"
    FAILED = "failed"


class RewardDeliveryStatus(str, Enum):
    RESERVED = "reserved"
    IN_PRODUCTION = "in_production"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    DIGITAL_SENT = "digital_sent"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Role(str, Enum):
    AUTHOR = "author"
    BACKER = "backer"
    MODERATOR = "moderator"
    ADMIN = "admin"


class SearchSort(str, Enum):
    NEWEST = "newest"
    POPULAR = "popular"
    ENDING_SOON = "ending_soon"


class ProjectCreateRequest(BaseModel):
    title: str = Field(min_length=5, max_length=120)
    short_description: str = Field(min_length=20, max_length=280)
    description: str = Field(min_length=80)
    video_url: str | None = None
    goal_amount: float = Field(gt=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    starts_at: datetime
    ends_at: datetime
    funding_model: FundingModel
    category: ProjectCategory
    tags: list[str] = Field(default_factory=list)
    author_id: str
    actor_role: Role


class Project(BaseModel):
    project_id: str
    title: str
    short_description: str
    description: str
    video_url: str | None = None
    goal_amount: float = Field(gt=0)
    pledged_amount: float = Field(default=0, ge=0)
    currency: str = "RUB"
    starts_at: datetime
    ends_at: datetime
    funding_model: FundingModel
    category: ProjectCategory
    tags: list[str] = Field(default_factory=list)
    author_id: str
    moderation_status: ModerationStatus = ModerationStatus.PENDING
    status: ProjectStatus = ProjectStatus.MODERATION
    backers_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProjectModerationRequest(BaseModel):
    approve: bool
    reason: str | None = None
    actor_id: str
    actor_role: Role


class ProjectPledgeUpdateRequest(BaseModel):
    amount: float = Field(gt=0)
    backer_id: str
    actor_role: Role


class ProjectDynamicGoalRequest(BaseModel):
    new_goal_amount: float = Field(gt=0)
    reason: str = Field(min_length=5)
    actor_id: str
    actor_role: Role


class PaymentCreateRequest(BaseModel):
    user_id: str
    project_id: str
    amount: float = Field(gt=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    method: PaymentMethod
    actor_role: Role


class PaymentRecord(BaseModel):
    payment_id: str
    user_id: str
    project_id: str
    amount: float = Field(gt=0)
    currency: str
    method: PaymentMethod
    commission_fee: float = Field(ge=0)
    net_amount: float = Field(ge=0)
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    refunded_at: datetime | None = None


class RefundRequest(BaseModel):
    reason: str = Field(min_length=3)
    actor_id: str
    actor_role: Role


class RewardTierCreateRequest(BaseModel):
    project_id: str
    title: str = Field(min_length=3, max_length=90)
    description: str = Field(min_length=10, max_length=500)
    min_amount: float = Field(gt=0)
    quantity: int | None = Field(default=None, ge=1)
    delivery_estimate_days: int | None = Field(default=None, ge=0)
    digital_delivery: bool = False
    actor_id: str
    actor_role: Role


class RewardTier(BaseModel):
    tier_id: str
    project_id: str
    title: str
    description: str
    min_amount: float = Field(gt=0)
    quantity: int | None = Field(default=None, ge=0)
    delivery_estimate_days: int | None = Field(default=None, ge=0)
    digital_delivery: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RewardAssignRequest(BaseModel):
    user_id: str
    project_id: str
    reward_id: str
    pledge_amount: float = Field(gt=0)
    actor_id: str
    actor_role: Role


class RewardAssignment(BaseModel):
    assignment_id: str
    user_id: str
    project_id: str
    reward_id: str
    delivery_status: RewardDeliveryStatus = RewardDeliveryStatus.RESERVED
    tracking_code: str | None = None
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RewardDeliveryUpdateRequest(BaseModel):
    status: RewardDeliveryStatus
    tracking_code: str | None = None
    actor_id: str
    actor_role: Role


class ProjectUpdateCreateRequest(BaseModel):
    project_id: str
    author_id: str
    title: str = Field(min_length=5, max_length=120)
    body: str = Field(min_length=30)
    is_voice: bool = False
    audio_url: str | None = None
    actor_role: Role


class ProjectUpdatePost(BaseModel):
    update_id: str
    project_id: str
    author_id: str
    title: str
    body: str
    is_voice: bool = False
    audio_url: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CommentCreateRequest(BaseModel):
    project_id: str
    user_id: str
    text: str = Field(min_length=2, max_length=1200)
    parent_id: str | None = None
    actor_role: Role


class Comment(BaseModel):
    comment_id: str
    project_id: str
    user_id: str
    text: str
    parent_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DirectMessageRequest(BaseModel):
    sender_id: str
    recipient_id: str
    text: str = Field(min_length=1, max_length=2000)
    actor_role: Role


class DirectMessage(BaseModel):
    message_id: str
    sender_id: str
    recipient_id: str
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_read: bool = False


class SearchIndexDocument(BaseModel):
    project_id: str
    title: str
    short_description: str
    category: ProjectCategory
    funding_model: FundingModel
    tags: list[str] = Field(default_factory=list)
    goal_amount: float = Field(gt=0)
    pledged_amount: float = Field(ge=0)
    status: ProjectStatus
    author_id: str
    created_at: datetime
    updated_at: datetime


class RecommendationRequest(BaseModel):
    user_id: str
    interests: list[str] = Field(default_factory=list)
    viewed_project_ids: list[str] = Field(default_factory=list)


class AnalyticsVisitEvent(BaseModel):
    project_id: str
    user_id: str | None = None
    source: str = "direct"


class AnalyticsPledgeEvent(BaseModel):
    project_id: str
    author_id: str
    user_id: str
    amount: float = Field(gt=0)
    goal_amount: float = Field(gt=0)


class AnalyticsRefundEvent(BaseModel):
    project_id: str
    author_id: str
    amount: float = Field(gt=0)


class NotificationRequest(BaseModel):
    channel: NotificationChannel
    recipient: str
    subject: str
    body: str
    severity: Severity = Severity.INFO
    actor_role: Role


class AuthorPledgeNotificationRequest(BaseModel):
    author_id: str
    project_id: str
    amount: float = Field(gt=0)
    currency: str = "RUB"
    actor_role: Role


class BackerStatusNotificationRequest(BaseModel):
    recipient_id: str
    project_id: str
    status: str
    actor_role: Role


class AuditEvent(BaseModel):
    event_id: str
    actor_id: str
    actor_role: Role | str
    action: str
    object_type: str
    object_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PledgeWorkflowRequest(BaseModel):
    user_id: str
    project_id: str
    amount: float = Field(gt=0)
    reward_id: str | None = None
    payment_method: PaymentMethod = PaymentMethod.CARD
    actor_role: Role = Role.BACKER


class PledgeWorkflowResult(BaseModel):
    project: dict[str, Any]
    payment: dict[str, Any]
    reward_assignment: dict[str, Any] | None = None
    notification: dict[str, Any]
    analytics: dict[str, Any]
    pledged_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
