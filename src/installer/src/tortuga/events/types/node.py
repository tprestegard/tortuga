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

from marshmallow import fields

from .base import BaseEventSchema, BaseEvent


class NodeStateChangedSchema(BaseEventSchema):
    """
    Schema for the NodeStateChange events.

    """
    node = fields.Dict()
    previous_state = fields.String()


class NodeStateChanged(BaseEvent):
    """
    Event that fires when a node state changes.

    """
    name = 'node-state-changed'
    schema_class = NodeStateChangedSchema

    def __init__(self, node: dict, previous_state: str, **kwargs):
        """
        Initializer.

        :param str node:     the current state of the node affected
        :param dict request: the previous state
        :param kwargs:

        """
        super().__init__(**kwargs)
        self.node: dict = node
        self.previous_state: str = previous_state


class NodeTagsChangedSchema(BaseEventSchema):
    """
    Schema for the NodeTagsChanged events.

    """
    node_id = fields.String
    node_name = fields.String
    tags = fields.Dict()
    previous_tags = fields.Dict()


class NodeTagsChanged(BaseEvent):
    """
    Event that fires when a node tags are changed.

    """
    name = 'node-tags-changed'
    schema_class = NodeTagsChangedSchema

    def __init__(self, node_id: str, node_name: str, tags: dict,
                 previous_tags: dict, **kwargs):
        """
        Initializer.

        :param dict node:          the current state of the nodeprofile
        :param dict previous_tags: the previous version of the tags for the
                                   node
        :param kwargs:

        """
        super().__init__(**kwargs)
        self.node_id = node_id
        self.node_name = node_name
        self.tags = tags
        self.previous_tags = previous_tags
