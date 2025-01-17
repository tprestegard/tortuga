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
import logging
from typing import Dict, Iterator, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session, sessionmaker

from tortuga.db.dbManager import DbManager
from tortuga.db.models.softwareProfile import SoftwareProfile as DbSoftwareProfile
from tortuga.db.models.softwareProfileTag import SoftwareProfileTag
from tortuga.events.types.software_profile import SoftwareProfileTagsChanged
from tortuga.objectstore.base import matches_filters
from tortuga.typestore.base import TypeStore
from .types import SoftwareProfile
from tortuga.wsapi.syncWsApi import SyncWsApi


logger = logging.getLogger(__name__)


class SqlalchemySessionSoftwareProfileStore(TypeStore):
    """
    An implementation of the TypeStore class for SoftwareProfile objects, backed
    by an Sqlalchemy database session.

    """
    type_class = SoftwareProfile

    def __init__(self, db_manager: DbManager):
        self._Session = sessionmaker(bind=db_manager.engine)

    def _to_db_swp(self, swp: SoftwareProfile, session: Session) -> Optional[DbSoftwareProfile]:
        if swp.id:
            db_swp = session.query(DbSoftwareProfile).filter(
                DbSoftwareProfile.id == int(swp.id)).first()
            if not db_swp:
                return None
        else:
            raise Exception('Creating swps is currently not supported')
        db_swp.name = swp.name
        db_swp.description = swp.description
        db_swp.minNodes = swp.min_nodes
        db_swp.maxNodes = swp.max_nodes
        db_swp.lockedState = swp.locked
        db_swp.dataRoot = swp.data_root
        db_swp.dataRsync = swp.data_rsync
        self._set_db_swp_tags(db_swp, swp.tags)
        return db_swp

    def _set_db_swp_tags(self, db_swp: DbSoftwareProfile, tags: Dict[str, str]):
        if not tags:
            tags = {}
        tags_to_delete = {tag.name: tag for tag in db_swp.tags}
        for name, value in tags.items():
            if name in tags_to_delete.keys():
                tag = tags_to_delete.pop(name)
                tag.value = value
            else:
                db_swp.tags.append(
                    SoftwareProfileTag(name=name, value=value)
                )
        for tag in tags_to_delete.values():
            db_swp.tags.remove(tag)

    def _to_swp(self, db_swp: DbSoftwareProfile) -> SoftwareProfile:
        return SoftwareProfile(
            id=str(db_swp.id),
            name=db_swp.name,
            description=db_swp.description,
            min_nodes=db_swp.minNodes,
            max_nodes=db_swp.maxNodes,
            locked=db_swp.lockedState,
            data_root=db_swp.dataRoot,
            data_rsync=db_swp.dataRsync,
            tags={tag.name: tag.value for tag in db_swp.tags}
        )

    def list(
            self,
            order_by: Optional[str] = None,
            order_desc: bool = False,
            order_alpha: bool = False,
            limit: Optional[int] = None,
            **filters) -> Iterator[SoftwareProfile]:
        logger.debug(
            'list(order_by=%s, order_desc=%s, limit=%s, filters=%s) -> ...',
            order_by, order_desc, limit, filters)
        session = self._Session()
        result = session.query(DbSoftwareProfile)
        if order_by:
            #
            # Note: currently, order_alpha is ignored for SqlAlchemy,
            #       as it is the default behavior for strings
            #
            if desc:
                result = result.order_by(desc(getattr(DbSoftwareProfile, order_by)))
            else:
                result = result.order_by(getattr(DbSoftwareProfile, order_by))
        count = 0
        for db_swp in result:
            swp = self._to_swp(db_swp)
            if matches_filters(swp, filters):
                logger.debug('list(...) -> %s', swp)
                count += 1
                if limit and count == limit:
                    yield swp
                    session.close()
                    return
                yield swp

    def get(self, obj_id: str) -> Optional[SoftwareProfile]:
        logger.debug('get(obj_id=%s) -> ...', obj_id)

        session = self._Session()
        db_swp = session.query(DbSoftwareProfile).filter(
            DbSoftwareProfile.id == int(obj_id)).first()
        swp = self._to_swp(db_swp)
        session.close()

        logger.debug('get(...) -> %s', swp)
        return swp

    def save(self, obj: SoftwareProfile) -> SoftwareProfile:
        logger.debug('save(obj=%s) -> ...', obj)

        swp_old = None
        if obj.id:
            swp_old = self.get(obj.id)

        session = self._Session()
        db_swp = self._to_db_swp(obj, session)
        if not db_swp:
            raise Exception('SoftwareProfile ID not found: %s', obj.id)
        session.commit()
        swp = self._to_swp(db_swp)
        session.close()

        self._fire_events(swp_old, swp)
        logger.debug('save(...) -> %s', swp)
        return swp

    def _marshall(self, swp: SoftwareProfile) -> dict:
        schema_class = SoftwareProfile.get_schema_class()
        marshalled = schema_class().dump(swp)
        return marshalled.data

    def _fire_events(self, swp_old: SoftwareProfile, swp: SoftwareProfile):
        self._event_tags_changed(swp_old, swp)

    def _event_tags_changed(self, swp_old: SoftwareProfile,
                            swp: SoftwareProfile):
        if swp_old.tags != swp.tags:
            SoftwareProfileTagsChanged.fire(
                softwareprofile_id=str(swp.id),
                softwareprofile_name=swp.name,
                tags=swp.tags,
                previous_tags=swp_old.tags
            )
            opts = {}
            opts['software_profile'] = {
                'id' : str(swp.id),
                'name' : swp.name,
                'tags' : swp.tags,
                'previous_tags' : swp_old.tags
            }
            logger.debug('Triggering cluster update with tags parameter: {}'.format(opts))
            SyncWsApi().scheduleClusterUpdate(updateReason='Software profile tags updated', opts=opts)
