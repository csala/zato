# -*- coding: utf-8 -*-

"""
Copyright (C) 2010 Dariusz Suchojad <dsuch at gefira.pl>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from json import dumps

# SQLAlchemy
from sqlalchemy import Table, Column, Integer, String, DateTime, MetaData, \
     ForeignKey, Sequence, Boolean, LargeBinary, UniqueConstraint, Enum, \
     SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship

# Zato
from zato.common.util import make_repr, object_attrs
from zato.common.odb import AMQP_DEFAULT_PRIORITY, WMQ_DEFAULT_PRIORITY

Base = declarative_base()

################################################################################

def to_json(model):
    """ Returns a JSON representation of an SQLAlchemy-backed object.
    """
    json = {}
    json['fields'] = {}
    json['pk'] = getattr(model, 'id')

    for col in model._sa_class_manager.mapper.mapped_table.columns:
        json['fields'][col.name] = getattr(model, col.name)

    return dumps([json])

class ZatoInstallState(Base):
    """ Contains a row for each Zato installation belonging to that particular
    ODB. For instance, installing Zato 1.0 will add a new row, installing 1.1
    """
    __tablename__ = 'install_state'

    id = Column(Integer,  Sequence('install_state_seq'), primary_key=True)
    version = Column(String(200), unique=True, nullable=False)
    install_time = Column(DateTime(), nullable=False)
    source_host = Column(String(200), nullable=False)
    source_user = Column(String(200), nullable=False)

    def __init__(self, id=None, version=None, install_time=None, source_host=None,
                 source_user=None):
        self.id = id
        self.version = version
        self.install_time = install_time
        self.source_host = source_host
        self.source_user = source_user

class Cluster(Base):
    """ Represents a Zato cluster.
    """
    __tablename__ = 'cluster'

    id = Column(Integer,  Sequence('cluster_id_seq'), primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    description = Column(String(1000), nullable=True)
    odb_type = Column(String(30), nullable=False)
    odb_host = Column(String(200), nullable=False)
    odb_port = Column(Integer(), nullable=False)
    odb_user = Column(String(200), nullable=False)
    odb_db_name = Column(String(200), nullable=False)
    odb_schema = Column(String(200), nullable=True)
    broker_host = Column(String(200), nullable=False)
    broker_start_port = Column(Integer(), nullable=False)
    broker_token = Column(String(32), nullable=False)
    lb_host = Column(String(200), nullable=False)
    lb_agent_port = Column(Integer(), nullable=False)
    lb_port = Column(Integer(), nullable=False)

    def __init__(self, id=None, name=None, description=None, odb_type=None,
                 odb_host=None, odb_port=None, odb_user=None, odb_db_name=None,
                 odb_schema=None, broker_host=None, broker_start_port=None,
                 broker_token=None, lb_host=None, lb_agent_port=None, 
                 lb_port=None):
        self.id = id
        self.name = name
        self.description = description
        self.odb_type = odb_type
        self.odb_host = odb_host
        self.odb_port = odb_port
        self.odb_user = odb_user
        self.odb_db_name = odb_db_name
        self.odb_schema = odb_schema
        self.broker_host = broker_host
        self.broker_start_port = broker_start_port
        self.broker_token = broker_token
        self.lb_host = lb_host
        self.lb_agent_port = lb_agent_port
        self.lb_port = lb_port

    def __repr__(self):
        return make_repr(self)

    def to_json(self):
        return to_json(self)

class Server(Base):
    """ Represents a Zato server.
    """
    __tablename__ = 'server'
    __table_args__ = (UniqueConstraint('name', 'cluster_id'), {})

    id = Column(Integer,  Sequence('server_id_seq'), primary_key=True)
    name = Column(String(200), nullable=False)
    
    last_join_status = Column(String(40), nullable=True)
    last_join_mod_date = Column(DateTime(timezone=True), nullable=True)
    last_join_mod_by = Column(String(200), nullable=True)
    
    odb_token = Column(String(32), nullable=False)

    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'), nullable=False)
    cluster = relationship(Cluster, backref=backref('servers', order_by=name, cascade='all, delete, delete-orphan'))
    
    def __init__(self, id=None, name=None, cluster=None, odb_token=None,
                 last_join_status=None, last_join_mod_date=None, last_join_mod_by=None):
        self.id = id
        self.name = name
        self.cluster = cluster
        self.odb_token = odb_token
        self.last_join_status = last_join_status
        self.last_join_mod_date = last_join_mod_date
        self.last_join_mod_by = last_join_mod_by

    def __repr__(self):
        return make_repr(self)
    
################################################################################

class ChannelURLSecurity(Base):
    """ An association table for the many-to-many mapping bettween channel URL
        definitions and security definitions.
    """
    __tablename__ = 'channel_url_security'
    
    id = Column(Integer, primary_key=True)
    
    channel_url_def_id = Column(Integer, ForeignKey('channel_url_def.id'))
    channel_url_def = relationship('ChannelURLDefinition', 
                        backref=backref('channel_url_security', uselist=False))
    
    security_def_id = Column(Integer, ForeignKey('security_def.id', ondelete='CASCADE'), nullable=False)
    security_def = relationship('SecurityDefinition', 
                    backref=backref('channel_url_security_defs', order_by=id, cascade='all, delete, delete-orphan'))
    
    def __init__(self, channel_url_def, security_def):
        self.channel_url_def = channel_url_def
        self.security_def = security_def
    
################################################################################

class SecurityDefinition(Base):
    """ A security definition
    """
    __tablename__ = 'security_def'
    
    id = Column(Integer,  Sequence('security_def_id_seq'), primary_key=True)
    security_def_type = Column(String(45), nullable=False)
    
    def __init__(self, id=None, security_def_type=None):
        self.id = id
        self.security_def_type = security_def_type
        
    def __repr__(self):
        return make_repr(self)

################################################################################

class ChannelURLDefinition(Base):
    """ A channel's URL definition.
    """
    __tablename__ = 'channel_url_def'
    __table_args__ = (UniqueConstraint('cluster_id', 'url_pattern'), {})

    id = Column(Integer,  Sequence('channel_url_def_id_seq'), primary_key=True)
    url_pattern = Column(String(400), nullable=False)
    url_type = Column(String(45), nullable=False)
    is_internal = Column(Boolean(), nullable=False)

    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'), nullable=False)
    cluster = relationship(Cluster, backref=backref('channel_url_defs', order_by=url_pattern, cascade='all, delete, delete-orphan'))
    
    def __init__(self, id=None, url_pattern=None, url_type=None, is_internal=None,
                 cluster=None):
        self.id = id
        self.url_pattern = url_pattern
        self.url_type = url_type
        self.is_internal = is_internal
        self.cluster = cluster

    def __repr__(self):
        return make_repr(self)

################################################################################

class WSSDefinition(Base):
    """ A WS-Security definition.
    """
    __tablename__ = 'wss_def'
    __table_args__ = (UniqueConstraint('cluster_id', 'name'), {})

    id = Column(Integer,  Sequence('wss_def_id_seq'), primary_key=True)
    name = Column(String(200), nullable=False)
    username = Column(String(200), nullable=False)
    password = Column(String(200), nullable=False)
    password_type = Column(String(45), nullable=False)
    reject_empty_nonce_ts = Column(Boolean(), nullable=False)
    reject_stale_username = Column(Boolean(), nullable=True)
    expiry_limit = Column(Integer(), nullable=False)
    nonce_freshness = Column(Integer(), nullable=True)
    
    is_active = Column(Boolean(), nullable=False)

    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'), nullable=False)
    cluster = relationship(Cluster, backref=backref('wss_defs', order_by=name, cascade='all, delete, delete-orphan'))
    
    security_def_id = Column(Integer, ForeignKey('security_def.id'), nullable=True)
    security_def = relationship(SecurityDefinition, backref=backref('wss_def', order_by=name, uselist=False, cascade='all, delete, delete-orphan'))
    
    def __init__(self, id=None, name=None, is_active=None, username=None, 
                 password=None, password_type=None, reject_empty_nonce_ts=None, 
                 reject_stale_username=None, expiry_limit=None, 
                 nonce_freshness=None, cluster=None, password_type_raw=None):
        self.id = id
        self.name = name
        self.is_active = is_active
        self.username = username
        self.password = password
        self.password_type = password_type
        self.reject_empty_nonce_ts = reject_empty_nonce_ts
        self.reject_stale_username = reject_stale_username
        self.expiry_limit = expiry_limit
        self.nonce_freshness = nonce_freshness
        self.cluster = cluster
        self.password_type_raw = password_type_raw

    def __repr__(self):
        return make_repr(self)
    
class HTTPBasicAuth(Base):
    """ An HTTP Basic Auth definition.
    """
    __tablename__ = 'http_basic_auth_def'
    __table_args__ = (UniqueConstraint('cluster_id', 'name'), {})

    id = Column(Integer,  Sequence('http_b_auth_def_id_seq'), primary_key=True)
    name = Column(String(200), nullable=False)
    username = Column(String(200), nullable=False)
    domain = Column(String(200), nullable=False)
    password = Column(String(200), nullable=False)
    
    is_active = Column(Boolean(), nullable=False)

    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'), nullable=False)
    cluster = relationship(Cluster, backref=backref('http_basic_auth_defs', order_by=name, cascade='all, delete, delete-orphan'))
    
    security_def_id = Column(Integer, ForeignKey('security_def.id'), nullable=True)
    security_def = relationship(SecurityDefinition, backref=backref('http_basic_auth_def', order_by=name, uselist=False))
    
    def __init__(self, id=None, name=None, is_active=None, username=None, 
                 domain=None, password=None, cluster=None):
        self.id = id
        self.name = name
        self.is_active = is_active
        self.username = username
        self.domain = domain
        self.password = password
        self.cluster = cluster

    def __repr__(self):
        return make_repr(self)

class TechnicalAccount(Base):
    """ Stores information about technical accounts, used for instance by Zato
    itself for securing access to its API.
    """
    __tablename__ = 'tech_account'
    __table_args__ = (UniqueConstraint('name'), {})
    
    id = Column(Integer,  Sequence('tech_account_id_seq'), primary_key=True)
    name = Column(String(45), nullable=False)
    password = Column(String(64), nullable=False)
    salt = Column(String(32), nullable=False)
    is_active = Column(Boolean(), nullable=False)
    
    security_def_id = Column(Integer, ForeignKey('security_def.id'), nullable=True)
    security_def = relationship(SecurityDefinition, backref=backref('tech_account', order_by=id, uselist=False))
    
    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'), nullable=False)
    cluster = relationship(Cluster, backref=backref('tech_accounts', order_by=name, cascade='all, delete, delete-orphan'))
    
    def __init__(self, id=None, name=None, password=None, salt=None, 
                 is_active=None, security_def=None, expected_password=None,
                 cluster=None):
        self.id = id
        self.name = name
        self.password = password
        self.salt = salt
        self.is_active = is_active
        self.security_def = security_def
        self.expected_password = expected_password
        self.cluster = cluster
        
    def to_json(self):
        return to_json(self)

################################################################################

class SQLConnectionPool(Base):
    """ An SQL connection pool.
    """
    __tablename__ = 'sql_pool'
    __table_args__ = (UniqueConstraint('cluster_id', 'name'), {})

    id = Column(Integer,  Sequence('sql_pool_id_seq'), primary_key=True)
    name = Column(String(200), nullable=False)
    user = Column(String(200), nullable=False)
    db_name = Column(String(200), nullable=False)
    engine = Column(String(200), nullable=False)
    extra = Column(LargeBinary(200000), nullable=True)
    host = Column(String(200), nullable=False)
    port = Column(Integer(), nullable=False)
    pool_size = Column(Integer(), nullable=False)

    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'), nullable=False)
    cluster = relationship(Cluster, backref=backref('sql_pools', order_by=name, cascade='all, delete, delete-orphan'))
    
    def __init__(self, id=None, name=None, db_name=None, user=None, engine=None,
                 extra=None, host=None, port=None, pool_size=None, cluster=None):
        self.id = id
        self.name = name
        self.db_name = db_name
        self.user = user
        self.engine = engine
        self.extra = extra
        self.host = host
        self.port = port
        self.pool_size = pool_size
        self.cluster = cluster

    def __repr__(self):
        return make_repr(self)

class SQLConnectionPoolPassword(Base):
    """ An SQL connection pool's passwords.
    """
    __tablename__ = 'sql_pool_passwd'

    id = Column(Integer,  Sequence('sql_pool_id_seq'), primary_key=True)
    password = Column(LargeBinary(200000), server_default='not-set-yet', nullable=False)
    server_key_hash = Column(LargeBinary(200000), server_default='not-set-yet', nullable=False)

    server_id = Column(Integer, ForeignKey('server.id', ondelete='CASCADE'), nullable=False)
    server = relationship(Server, backref=backref('sql_pool_passwords', order_by=id, cascade='all, delete, delete-orphan'))

    sql_pool_id = Column(Integer, ForeignKey('sql_pool.id', ondelete='CASCADE'), nullable=False)
    sql_pool = relationship(SQLConnectionPool, backref=backref('sql_pool_passwords', order_by=id, cascade='all, delete, delete-orphan'))
    
    def __init__(self, id=None, password=None, server_key_hash=None, server_id=None,
                 server=None, sql_pool_id=None, sql_pool=None):
        self.id = id
        self.password = password
        self.server_key_hash = server_key_hash
        self.server_id = server_id
        self.server = server
        self.sql_pool_id = sql_pool_id
        self.sql_pool = sql_pool

    def __repr__(self):
        return make_repr(self)


################################################################################

class Service(Base):
    """ A set of basic informations about a service available in a given cluster.
    """
    __tablename__ = 'service'
    __table_args__ = (UniqueConstraint('name', 'cluster_id'), {})
    
    id = Column(Integer,  Sequence('service_id_seq'), primary_key=True)
    name = Column(String(2000), nullable=False)
    is_active = Column(Boolean(), nullable=False)
    impl_name = Column(String(2000), nullable=False)
    is_internal = Column(Boolean(), nullable=False)
    
    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'), nullable=False)
    cluster = relationship(Cluster, backref=backref('services', order_by=name, cascade='all, delete, delete-orphan'))
    
    def __init__(self, id=None, name=None, impl_name=None, is_internal=None, 
                 is_active=None, cluster=None):
        self.id = id
        self.name = name
        self.impl_name = impl_name
        self.is_internal = is_internal
        self.is_active = is_active
        self.cluster = cluster
    
class DeployedService(Base):
    """ A service living on a given server.
    """
    __tablename__ = 'deployed_service'
    __table_args__ = (UniqueConstraint('server_id', 'service_id'), {})
    
    deployment_time = Column(DateTime(), nullable=False)
    details = Column(String(2000), nullable=False)

    server_id = Column(Integer, ForeignKey('server.id', ondelete='CASCADE'), nullable=False, primary_key=True)
    server = relationship(Server, backref=backref('deployed_services', order_by=deployment_time, cascade='all, delete, delete-orphan'))
    
    service_id = Column(Integer, ForeignKey('service.id', ondelete='CASCADE'), nullable=False, primary_key=True)
    service = relationship(Service, backref=backref('deployment_data', order_by=deployment_time, cascade='all, delete, delete-orphan'))
    
    def __init__(self, deployment_time, details, server, service):
        self.deployment_time = deployment_time
        self.details = details
        self.server = server
        self.service = service
    
################################################################################

class Job(Base):
    """ A scheduler's job. Stores all the information needed to execute a job
    if it's a one-time job, otherwise the information is kept in related tables.
    """
    __tablename__ = 'job'
    __table_args__ = (UniqueConstraint('name', 'cluster_id'), {})
    
    id = Column(Integer,  Sequence('job_id_seq'), primary_key=True)
    name = Column(String(200), nullable=False)
    is_active = Column(Boolean(), nullable=False)
    job_type = Column(Enum('one_time', 'interval_based', 'cron_style', 
                           name='job_type'), nullable=False)
    start_date = Column(DateTime(), nullable=False)
    extra = Column(LargeBinary(400000), nullable=True)
    
    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'), nullable=False)
    cluster = relationship(Cluster, backref=backref('jobs', order_by=name, cascade='all, delete, delete-orphan'))
    
    service_id = Column(Integer, ForeignKey('service.id', ondelete='CASCADE'), nullable=False)
    service = relationship(Service, backref=backref('jobs', order_by=name, cascade='all, delete, delete-orphan'))
    
    def __init__(self, id=None, name=None, is_active=None, job_type=None, 
                 start_date=None, extra=None, cluster=None, cluster_id=None,
                 service=None, service_id=None, service_name=None, interval_based=None, 
                 cron_style=None, definition_text=None, job_type_friendly=None):
        self.id = id
        self.name = name
        self.is_active = is_active
        self.job_type = job_type
        self.start_date = start_date
        self.extra = extra
        self.cluster = cluster
        self.cluster_id = cluster_id
        self.service = service
        self.service_id = service_id
        self.service_name = service_name # Not used by the database
        self.interval_based = interval_based
        self.cron_style = cron_style
        self.definition_text = definition_text # Not used by the database
        self.job_type_friendly = job_type_friendly # Not used by the database
    
class IntervalBasedJob(Base):
    """ A Cron-style scheduler's job.
    """
    __tablename__ = 'job_interval_based'
    __table_args__ = (UniqueConstraint('job_id'), {})
    
    id = Column(Integer,  Sequence('job_intrvl_seq'), primary_key=True)
    job_id = Column(Integer, nullable=False)
    
    weeks = Column(Integer, nullable=True)
    days = Column(Integer, nullable=True)
    hours = Column(Integer, nullable=True)
    minutes = Column(Integer, nullable=True)
    seconds = Column(Integer, nullable=True)
    repeats = Column(Integer, nullable=True)
    
    job_id = Column(Integer, ForeignKey('job.id', ondelete='CASCADE'), nullable=False)
    job = relationship(Job, backref=backref('interval_based', uselist=False, cascade='all, delete, delete-orphan', single_parent=True))
    
    def __init__(self, id=None, job=None, weeks=None, days=None, hours=None,
                 minutes=None, seconds=None, repeats=None, definition_text=None):
        self.id = id
        self.job = job
        self.weeks = weeks
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.repeats = repeats
        self.definition_text = definition_text # Not used by the database
    
class CronStyleJob(Base):
    """ A Cron-style scheduler's job.
    """
    __tablename__ = 'job_cron_style'
    __table_args__ = (UniqueConstraint('job_id'), {})
    
    id = Column(Integer,  Sequence('job_cron_seq'), primary_key=True)
    cron_definition = Column(String(4000), nullable=False)
    
    job_id = Column(Integer, ForeignKey('job.id', ondelete='CASCADE'), nullable=False)
    job = relationship(Job, backref=backref('cron_style', uselist=False, cascade='all, delete, delete-orphan', single_parent=True))
    
    def __init__(self, id=None, job=None, cron_definition=None):
        self.id = id
        self.job = job
        self.cron_definition = cron_definition

################################################################################

class ConnDefAMQP(Base):
    """ An AMQP connection definition.
    """
    __tablename__ = 'conn_def_amqp'
    __table_args__ = (UniqueConstraint('name', 'cluster_id', 'def_type'), {})
    
    id = Column(Integer,  Sequence('conn_def_amqp_seq'), primary_key=True)
    name = Column(String(200), nullable=False)
    def_type = Column(String(10), nullable=False)
    
    host = Column(String(200), nullable=False)
    port = Column(Integer(), nullable=False)
    vhost = Column(String(200), nullable=False)
    username = Column(String(200), nullable=False)
    password = Column(String(200), nullable=False)
    frame_max = Column(Integer(), nullable=False)
    heartbeat = Column(Integer(), nullable=False)
    
    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'), nullable=False)
    cluster = relationship(Cluster, backref=backref('amqp_conn_defs', order_by=name, cascade='all, delete, delete-orphan'))
    
    def __init__(self, id=None, name=None, def_type=None, host=None, port=None, 
                 vhost=None,  username=None,  password=None, frame_max=None, 
                 heartbeat=None, cluster_id=None):
        self.id = id
        self.name = name
        self.def_type = def_type
        self.host = host
        self.port = port
        self.vhost = vhost
        self.username = username
        self.password = password
        self.frame_max = frame_max
        self.heartbeat = heartbeat
        self.cluster_id = cluster_id
        
class ConnDefWMQ(Base):
    """ A WebSphere MQ connection definition.
    """
    __tablename__ = 'conn_def_wmq'
    __table_args__ = (UniqueConstraint('name', 'cluster_id'), {})
    
    id = Column(Integer,  Sequence('conn_def_wmq_seq'), primary_key=True)
    name = Column(String(200), nullable=False)
    
    host = Column(String(200), nullable=False)
    port = Column(Integer, nullable=False)
    queue_manager = Column(String(200), nullable=False)
    channel = Column(String(200), nullable=False)
    cache_open_send_queues = Column(Boolean(), nullable=False)
    cache_open_receive_queues = Column(Boolean(), nullable=False)
    use_shared_connections = Column(Boolean(), nullable=False)
    dynamic_queue_template = Column(String(200), nullable=False, server_default='SYSTEM.DEFAULT.MODEL.QUEUE') # We're not actually using it yet
    ssl = Column(Boolean(), nullable=False)
    ssl_cipher_spec = Column(String(200))
    ssl_key_repository = Column(String(200))
    needs_mcd = Column(Boolean(), nullable=False)
    max_chars_printed = Column(Integer, nullable=False)
    
    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'), nullable=False)
    cluster = relationship(Cluster, backref=backref('wmq_conn_defs', order_by=name, cascade='all, delete, delete-orphan'))
    
    def __init__(self, id=None, name=None, host=None, port=None, 
                 queue_manager=None, channel=None, cache_open_send_queues=None,  
                 cache_open_receive_queues=None,  use_shared_connections=None, ssl=None, 
                 ssl_cipher_spec=None, ssl_key_repository=None, needs_mcd=None,
                 max_chars_printed=None, cluster_id=None):
        self.id = id
        self.name = name
        self.host = host
        self.queue_manager = queue_manager
        self.channel = channel
        self.port = port
        self.cache_open_receive_queues = cache_open_receive_queues
        self.cache_open_send_queues = cache_open_send_queues
        self.use_shared_connections = use_shared_connections
        self.ssl = ssl
        self.ssl_cipher_spec = ssl_cipher_spec
        self.ssl_key_repository = ssl_key_repository
        self.needs_mcd = needs_mcd
        self.max_chars_printed = max_chars_printed
        self.cluster_id = cluster_id

################################################################################

class OutgoingAMQP(Base):
    """ An outgoing AMQP connection.
    """
    __tablename__ = 'out_amqp'
    
    id = Column(Integer,  Sequence('out_amqp_seq'), primary_key=True)
    name = Column(String(200), nullable=False)
    is_active = Column(Boolean(), nullable=False)
    
    delivery_mode = Column(SmallInteger(), nullable=False)
    priority = Column(SmallInteger(), server_default=str(AMQP_DEFAULT_PRIORITY), nullable=False)
    
    content_type = Column(String(200), nullable=True)
    content_encoding = Column(String(200), nullable=True)
    expiration = Column(String(20), nullable=True)
    user_id = Column(String(200), nullable=True)
    app_id = Column(String(200), nullable=True)
    
    def_id = Column(Integer, ForeignKey('conn_def_amqp.id', ondelete='CASCADE'), nullable=False)
    def_ = relationship(ConnDefAMQP, backref=backref('out_conns_amqp', cascade='all, delete, delete-orphan'))
    
    def __init__(self, id=None, name=None, is_active=None, delivery_mode=None,
                 priority=None, content_type=None, content_encoding=None, 
                 expiration=None, user_id=None, app_id=None, def_id=None,
                 delivery_mode_text=None, def_name=None):
        self.id = id
        self.name = name
        self.is_active = is_active
        self.delivery_mode = delivery_mode
        self.priority = priority
        self.content_type = content_type
        self.content_encoding = content_encoding
        self.expiration = expiration
        self.user_id = user_id
        self.app_id = app_id
        self.def_id = def_id
        self.delivery_mode_text = delivery_mode_text # Not used by the DB
        self.def_name = def_name # Not used by the DB
        
class OutgoingWMQ(Base):
    """ An outgoing WebSphere MQ connection.
    """
    __tablename__ = 'out_wmq'
    
    id = Column(Integer,  Sequence('out_wmq_seq'), primary_key=True)
    name = Column(String(200), nullable=False)
    is_active = Column(Boolean(), nullable=False)
    
    delivery_mode = Column(SmallInteger(), nullable=False)
    priority = Column(SmallInteger(), server_default=str(WMQ_DEFAULT_PRIORITY), nullable=False)
    expiration = Column(String(20), nullable=True)
    
    def_id = Column(Integer, ForeignKey('conn_def_wmq.id', ondelete='CASCADE'), nullable=False)
    def_ = relationship(ConnDefWMQ, backref=backref('out_conns_wmq', cascade='all, delete, delete-orphan'))
    
    def __init__(self, id=None, name=None, is_active=None, delivery_mode=None,
                 priority=None, expiration=None, def_id=None, delivery_mode_text=None, 
                 def_name=None):
        self.id = id
        self.name = name
        self.is_active = is_active
        self.delivery_mode = delivery_mode
        self.priority = priority
        self.expiration = expiration
        self.def_id = def_id
        self.delivery_mode_text = delivery_mode_text # Not used by the DB
        self.def_name = def_name # Not used by the DB
        
class OutgoingZMQ(Base):
    """ An outgoing Zero MQ connection.
    """
    __tablename__ = 'out_zmq'
    
    id = Column(Integer,  Sequence('out_zmq_seq'), primary_key=True)
    name = Column(String(200), nullable=False)
    is_active = Column(Boolean(), nullable=False)
    
    address = Column(String(200), nullable=False)
    socket_type = Column(String(20), nullable=False)
    
    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'), nullable=False)
    cluster = relationship(Cluster, backref=backref('out_conns_zmq', order_by=name, cascade='all, delete, delete-orphan'))
    
    def __init__(self, id=None, name=None, is_active=None, address=None,
                 socket_type=None, cluster_id=None):
        self.id = id
        self.name = name
        self.is_active = is_active
        self.socket_type = socket_type
        self.address = address
        self.cluster_id = cluster_id
        
################################################################################

class ChannelAMQP(Base):
    """ An incoming AMQP connection.
    """
    __tablename__ = 'channel_amqp'
    
    id = Column(Integer,  Sequence('channel_amqp_seq'), primary_key=True)
    name = Column(String(200), nullable=False)
    is_active = Column(Boolean(), nullable=False)
    queue = Column(String(200), nullable=False)
    consumer_tag_prefix = Column(String(200), nullable=False)

    service_id = Column(Integer, ForeignKey('service.id', ondelete='CASCADE'), nullable=False)
    service = relationship(Service, backref=backref('amqp_channels', order_by=name, cascade='all, delete, delete-orphan'))
    
    def_id = Column(Integer, ForeignKey('conn_def_amqp.id', ondelete='CASCADE'), nullable=False)
    def_ = relationship(ConnDefAMQP, backref=backref('channels_amqp', cascade='all, delete, delete-orphan'))
    
    def __init__(self, id=None, name=None, is_active=None, queue=None, 
                 consumer_tag_prefix=None, def_id=None, def_name=None,
                 service_name=None):
        self.id = id
        self.name = name
        self.is_active = is_active
        self.queue = queue
        self.consumer_tag_prefix = consumer_tag_prefix
        self.def_id = def_id
        self.def_name = def_name # Not used by the DB
        self.service_name = service_name # Not used by the DB
        
class ChannelWMQ(Base):
    """ An incoming WebSphere MQ connection.
    """
    __tablename__ = 'channel_wmq'
    
    id = Column(Integer,  Sequence('channel_wmq_seq'), primary_key=True)
    name = Column(String(200), nullable=False)
    is_active = Column(Boolean(), nullable=False)
    queue = Column(String(200), nullable=False)

    service_id = Column(Integer, ForeignKey('service.id', ondelete='CASCADE'), nullable=False)
    service = relationship(Service, backref=backref('wmq_channels', order_by=name, cascade='all, delete, delete-orphan'))
    
    def_id = Column(Integer, ForeignKey('conn_def_wmq.id', ondelete='CASCADE'), nullable=False)
    def_ = relationship(ConnDefWMQ, backref=backref('channels_wmq', cascade='all, delete, delete-orphan'))
    
    def __init__(self, id=None, name=None, is_active=None, queue=None, 
                 def_id=None, def_name=None, service_name=None):
        self.id = id
        self.name = name
        self.is_active = is_active
        self.queue = queue
        self.def_id = def_id
        self.def_name = def_name # Not used by the DB
        self.service_name = service_name # Not used by the DB

class ChannelZMQ(Base):
    """ An incoming Zero MQ connection.
    """
    __tablename__ = 'channel_zmq'
    
    id = Column(Integer,  Sequence('channel_zmq_seq'), primary_key=True)
    name = Column(String(200), nullable=False)
    is_active = Column(Boolean(), nullable=False)
    
    address = Column(String(200), nullable=False)
    socket_type = Column(String(20), nullable=False)
    sub_key = Column(String(200), nullable=True)
    
    cluster_id = Column(Integer, ForeignKey('cluster.id', ondelete='CASCADE'), nullable=False)
    cluster = relationship(Cluster, backref=backref('channels_zmq', order_by=name, cascade='all, delete, delete-orphan'))
    
    def __init__(self, id=None, name=None, is_active=None, address=None,
                 socket_type=None, sub_key=None, cluster_id=None):
        self.id = id
        self.name = name
        self.is_active = is_active
        self.address = address
        self.socket_type = socket_type
        self.sub_key = sub_key
        self.cluster_id = cluster_id