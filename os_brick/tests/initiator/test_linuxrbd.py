# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import mock

from os_brick.initiator import linuxrbd
from os_brick.tests import base


class RBDVolumeIOWrapperTestCase(base.TestCase):

    def setUp(self):
        super(RBDVolumeIOWrapperTestCase, self).setUp()
        self.mock_volume = mock.Mock()
        self.mock_volume_wrapper = \
            linuxrbd.RBDVolumeIOWrapper(self.mock_volume)
        self.data_length = 1024
        self.full_data = 'abcd' * 256

    def test_init(self):
        self.assertEqual(self.mock_volume,
                         self.mock_volume_wrapper._rbd_volume)
        self.assertEqual(0, self.mock_volume_wrapper._offset)

    def test_inc_offset(self):
        self.mock_volume_wrapper._inc_offset(10)
        self.mock_volume_wrapper._inc_offset(10)
        self.assertEqual(20, self.mock_volume_wrapper._offset)

    def test_read(self):

        def mock_read(offset, length):
            return self.full_data[offset:length]

        self.mock_volume.image.read.side_effect = mock_read
        self.mock_volume.image.size.return_value = self.data_length

        data = self.mock_volume_wrapper.read()
        self.assertEqual(self.full_data, data)

        data = self.mock_volume_wrapper.read()
        self.assertEqual('', data)

        self.mock_volume_wrapper.seek(0)
        data = self.mock_volume_wrapper.read()
        self.assertEqual(self.full_data, data)

        self.mock_volume_wrapper.seek(0)
        data = self.mock_volume_wrapper.read(10)
        self.assertEqual(self.full_data[:10], data)

    def test_write(self):
        self.mock_volume_wrapper.write(self.full_data)
        self.assertEqual(1024, self.mock_volume_wrapper._offset)

    def test_seekable(self):
        self.assertTrue(self.mock_volume_wrapper.seekable)

    def test_seek(self):
        self.assertEqual(0, self.mock_volume_wrapper._offset)
        self.mock_volume_wrapper.seek(10)
        self.assertEqual(10, self.mock_volume_wrapper._offset)
        self.mock_volume_wrapper.seek(10)
        self.assertEqual(10, self.mock_volume_wrapper._offset)
        self.mock_volume_wrapper.seek(10, 1)
        self.assertEqual(20, self.mock_volume_wrapper._offset)

        self.mock_volume_wrapper.seek(0)
        self.mock_volume_wrapper.write(self.full_data)
        self.mock_volume.image.size.return_value = self.data_length
        self.mock_volume_wrapper.seek(0)
        self.assertEqual(0, self.mock_volume_wrapper._offset)

        self.mock_volume_wrapper.seek(10, 2)
        self.assertEqual(self.data_length + 10,
                         self.mock_volume_wrapper._offset)
        self.mock_volume_wrapper.seek(-10, 2)
        self.assertEqual(self.data_length - 10,
                         self.mock_volume_wrapper._offset)

        # test exceptions.
        self.assertRaises(IOError, self.mock_volume_wrapper.seek, 0, 3)
        self.assertRaises(IOError, self.mock_volume_wrapper.seek, -1)
        # offset should not have been changed by any of the previous
        # operations.
        self.assertEqual(self.data_length - 10,
                         self.mock_volume_wrapper._offset)

    def test_tell(self):
        self.assertEqual(0, self.mock_volume_wrapper.tell())
        self.mock_volume_wrapper._inc_offset(10)
        self.assertEqual(10, self.mock_volume_wrapper.tell())

    def test_flush(self):
        with mock.patch.object(linuxrbd, 'LOG') as mock_logger:
            self.mock_volume.image.flush = mock.Mock()
            self.mock_volume_wrapper.flush()
            self.mock_volume.image.flush.assert_called_once()
            self.mock_volume.image.flush.reset_mock()
            # this should be caught and logged silently.
            self.mock_volume.image.flush.side_effect = AttributeError
            self.mock_volume_wrapper.flush()
            self.mock_volume.image.flush.assert_called_once()
            mock_logger.warning.assert_called_once()

    def test_fileno(self):
        self.assertRaises(IOError, self.mock_volume_wrapper.fileno)

    def test_close(self):
        self.mock_volume_wrapper.close()
