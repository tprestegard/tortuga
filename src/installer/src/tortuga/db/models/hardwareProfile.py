# Copyright 2008-2018 Univa Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=too-few-public-methods

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from .base import ModelBase


hardwareprofile_admins = Table(
    'hardwareprofile_admins',
    ModelBase.metadata,
    Column('hardwareProfileId', Integer, ForeignKey('hardwareprofiles.id')),
    Column('adminId', Integer, ForeignKey('admins.id'))
)


class HardwareProfile(ModelBase):
    __tablename__ = 'hardwareprofiles'

    id = Column(Integer, primary_key=True)
    name = Column(String(45), nullable=False, unique=True)
    description = Column(String(255))
    nameFormat = Column(String(45))
    installType = Column(String(20), nullable=False, default='package')
    kernel = Column(String(255))
    kernelParams = Column(String(512))
    initrd = Column(String(255))
    softwareOverrideAllowed = Column(Boolean, nullable=False, default=True)
    idleSoftwareProfileId = Column(Integer, ForeignKey('softwareprofiles.id'))
    location = Column(String(45), default='local')
    localBootParams = Column(String(255))
    resourceAdapterId = Column(Integer, ForeignKey('resourceadapters.id'))
    cost = Column(Integer, default=0)

    resourceAdapterConfigId = Column(
        Integer, ForeignKey('resource_adapter_config.id')
    )

    admins = relationship('Admin', secondary='hardwareprofile_admins',
                          backref='hardwareprofiles')
    hardwareprofilenetworks = relationship('HardwareProfileNetwork',
                                           backref='hardwareprofile',
                                           cascade="all,delete-orphan")
    nodes = relationship('Node', backref='hardwareprofile')

    nics = relationship('Nic',
                        secondary='hardwareprofile_provisioning_nics',
                        lazy=False)

    resourceadapter = relationship('ResourceAdapter',
                                   backref='hardwareprofiles')

    default_resource_adapter_config = relationship(
        'ResourceAdapterConfig', backref='hardwareprofiles'
    )

    tags = relationship('HardwareProfileTag', lazy=False,
                        cascade="all, delete-orphan")

    def __repr__(self):
        return '<HardwareProfile(name={})>'.format(self.name)
