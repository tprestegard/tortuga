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

from tortuga.objectstore.manager import ObjectStoreManager
from .store import ResourceRequestStore, ObjectStoreResourceRequestStore


class ResourceRequestStoreManager:
    """
    ResourceRequest store manager

    """
    _event_store: ResourceRequestStore = None

    @classmethod
    def get(cls) -> ResourceRequestStore:
        """
        Get an instance of the event store.

        :return EvemtStore:  the event store instance

        """
        if not cls._event_store:
            object_store = ObjectStoreManager.get('resourcerequests')
            cls._event_store = ObjectStoreResourceRequestStore(object_store)
        return cls._event_store

