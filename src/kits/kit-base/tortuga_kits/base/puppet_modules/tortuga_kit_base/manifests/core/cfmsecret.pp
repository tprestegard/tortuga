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


class tortuga_kit_base::core::cfmsecret {
  file { '/etc/cfm':
    ensure => directory,
    owner  => 'root',
    group  => 'root',
  }

  $record = Sensitive.new(lookup({"name" => "cfm", "default_value" => { "password" => ""} }))

  # Unwrap for hash lookup
  $processed = $record.unwrap
  $cfm_secret = Sensitive.new($processed['password'])

  if $cfm_secret.unwrap == "" {
    file { '/etc/cfm/.cfmsecret':
      source  => 'puppet:///private/.cfmsecret',
      owner   => 'root',
      group   => 'root',
      mode    => '0600',
      require => File['/etc/cfm'],
    }
  } else {
    file { '/etc/cfm/.cfmsecret':
      content  => $cfm_secret,
      owner   => 'root',
      group   => 'root',
      mode    => '0600',
      require => File['/etc/cfm'],
    }
  }
}
