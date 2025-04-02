from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Tenant(Base):
    __tablename__ = 'tenants'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_name = Column(String(255), nullable=False)
    tenant_description = Column(Text, nullable=False)
    tenant_email = Column(String(255), unique=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    gen_ai_services = relationship("GenAIService", back_populates="tenant", uselist=False)
    interviewer_services = relationship("InterviewerService", back_populates="tenant", uselist=False)
    database_services = relationship("DatabaseService", back_populates="tenant", uselist=False)
    cloud_services = relationship("CloudService", back_populates="tenant", uselist=False)


class GenAIService(Base):
    __tablename__ = 'gen_ai_services'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'))
    user_id = Column(String(255), nullable=False)
    enabled_action = Column(Boolean, default=False)
    ai_provider = Column(String(100), nullable=False)
    ai_model = Column(String(100), nullable=False)
    api_key = Column(String(255), nullable=False)
    tts_provider = Column(String(100), nullable=False)
    stt_provider = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationship
    tenant = relationship("Tenant", back_populates="gen_ai_services")


class InterviewerService(Base):
    __tablename__ = 'interviewer_services'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'))
    user_id = Column(String(255), nullable=False)
    enabled_action = Column(Boolean, default=False)
    interview_model = Column(String(100), nullable=False)
    ai_backend = Column(String(100), nullable=False)
    api_key = Column(String(255), nullable=False)
    voice_enabled = Column(String(10), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationship
    tenant = relationship("Tenant", back_populates="interviewer_services")


class DatabaseService(Base):
    __tablename__ = 'database_services'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'))
    user_id = Column(String(255), nullable=False)
    enabled_action = Column(Boolean, default=False)
    db_type = Column(String(50), nullable=False)
    db_host = Column(String(255), nullable=False)
    db_port = Column(String(10), nullable=False)
    db_name = Column(String(100), nullable=False)
    db_username = Column(String(100), nullable=False)
    db_password = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationship
    tenant = relationship("Tenant", back_populates="database_services")


class CloudService(Base):
    __tablename__ = 'cloud_services'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'))
    user_id = Column(String(255), nullable=False)
    enabled_action = Column(Boolean, default=False)
    cloud_provider = Column(String(50), nullable=False)
    cloud_region = Column(String(50), nullable=False)
    access_key_id = Column(String(255), nullable=False)
    secret_access_key = Column(String(255), nullable=False)
    service_level = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationship
    tenant = relationship("Tenant", back_populates="cloud_services")
