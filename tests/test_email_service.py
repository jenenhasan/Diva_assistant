import unittest
from unittest.mock import Mock, patch
from src.services.email import EmailService   


class TestEmailService(unittest.TestCase):
    """Unit tests for EmailService class."""

    def setUp(self):
        """Create a mock Gmail client and an EmailService instance."""
        self.mock_gmail = Mock()
        self.email_service = EmailService(gmail_client=self.mock_gmail)

    # -------------------------------------------------------------------------
    # Tests for _extract_name_email (helper)
    # -------------------------------------------------------------------------
    def test_extract_name_email_quoted(self):
        """Extract name and email from 'Name <email@example.com>' format."""
        name, email = self.email_service._extract_name_email('John Doe <john@example.com>')
        self.assertEqual(name, 'john doe')
        self.assertEqual(email, 'john@example.com')

    def test_extract_name_email_bare_email(self):
        """Extract from 'email@example.com' (no name)."""
        name, email = self.email_service._extract_name_email('jane@example.com')
        self.assertEqual(name, 'jane@example.com')
        self.assertEqual(email, 'jane@example.com')

    def test_extract_name_email_with_quotes(self):
        """Extract from '"Doe, John" <john.doe@example.com>'."""
        name, email = self.email_service._extract_name_email('"Doe, John" <john.doe@example.com>')
        self.assertEqual(name, 'doe, john')
        self.assertEqual(email, 'john.doe@example.com')

    # -------------------------------------------------------------------------
    # Tests for _get_all_contacts
    # -------------------------------------------------------------------------
    def test_get_all_contacts_from_recent_emails(self):
        """_get_all_contacts reads from recent messages and extracts contacts."""
        # Mock the Gmail list_messages response
        self.mock_gmail.list_messages.return_value = [
            {'id': 'msg1'},
            {'id': 'msg2'}
        ]
        # Mock get_message for each id
        def get_message_side_effect(msg_id):
            if msg_id == 'msg1':
                return {
                    'payload': {
                        'headers': [
                            {'name': 'From', 'value': 'Alice <alice@example.com>'},
                            {'name': 'To', 'value': 'Bob <bob@example.com>'}
                        ]
                    }
                }
            else:  # msg2
                return {
                    'payload': {
                        'headers': [
                            {'name': 'From', 'value': 'Charlie <charlie@example.com>'}
                        ]
                    }
                }
        self.mock_gmail.get_message.side_effect = get_message_side_effect

        contacts = self.email_service._get_all_contacts()

        expected = {
            'alice': 'alice@example.com',
            'bob': 'bob@example.com',
            'charlie': 'charlie@example.com'
        }
        self.assertEqual(contacts, expected)
        self.mock_gmail.list_messages.assert_called_once_with(max_results=50)

    # -------------------------------------------------------------------------
    # Tests for find_email_by_name (fuzzy matching)
    # -------------------------------------------------------------------------
    def test_find_email_by_name_exact_match(self):
        contacts = {'john doe': 'john@example.com', 'jane smith': 'jane@example.com'}
        result = self.email_service.find_email_by_name('john doe', contacts=contacts)
        self.assertEqual(result, 'john@example.com')

    def test_find_email_by_name_fuzzy_match(self):
        contacts = {'john doe': 'john@example.com', 'jane smith': 'jane@example.com'}
        result = self.email_service.find_email_by_name('jon doe', threshold=70, contacts=contacts)
        # Should match 'john doe' with high similarity
        self.assertEqual(result, 'john@example.com')

    def test_find_email_by_name_match_by_email_address(self):
        contacts = {'alice': 'alice.wonder@example.com', 'bob': 'bob@example.com'}
        result = self.email_service.find_email_by_name('alice.wonder', contacts=contacts)
        self.assertEqual(result, 'alice.wonder@example.com')

    def test_find_email_by_name_no_match_below_threshold(self):
        contacts = {'john doe': 'john@example.com'}
        result = self.email_service.find_email_by_name('completely different', threshold=90, contacts=contacts)
        self.assertIsNone(result)

    def test_find_email_by_name_uses_default_contacts_if_none_provided(self):
        # Mock _get_all_contacts to return a known dict
        with patch.object(self.email_service, '_get_all_contacts', return_value={'test': 'test@example.com'}):
            result = self.email_service.find_email_by_name('test')
            self.assertEqual(result, 'test@example.com')
            self.email_service._get_all_contacts.assert_called_once()

    # -------------------------------------------------------------------------
    # Tests for send_email
    # -------------------------------------------------------------------------
    def test_send_email_success(self):
        self.mock_gmail.send_message.return_value = {'id': '12345'}
        result = self.email_service.send_email('to@example.com', 'Subject', 'Body')
        self.assertTrue(result['success'])
        self.assertEqual(result['message_id'], '12345')
        self.mock_gmail.send_message.assert_called_once_with('to@example.com', 'Subject', 'Body')

    def test_send_email_failure(self):
        self.mock_gmail.send_message.side_effect = Exception('Network error')
        result = self.email_service.send_email('to@example.com', 'Subject', 'Body')
        self.assertFalse(result['success'])
        self.assertIn('Network error', result['error'])

    # -------------------------------------------------------------------------
    # Tests for read_emails_headlines
    # -------------------------------------------------------------------------
    def test_read_emails_headlines(self):
        # Mock list_messages response
        self.mock_gmail.list_messages.return_value = [
            {'id': 'msg1'},
            {'id': 'msg2'}
        ]
        # Mock get_message for each
        def get_message_side_effect(msg_id):
            if msg_id == 'msg1':
                return {
                    'payload': {
                        'headers': [
                            {'name': 'From', 'value': 'sender1@example.com'},
                            {'name': 'Subject', 'value': 'Hello'}
                        ]
                    },
                    'labelIds': ['UNREAD']
                }
            else:
                return {
                    'payload': {
                        'headers': [
                            {'name': 'From', 'value': 'sender2@example.com'},
                            {'name': 'Subject', 'value': 'Meeting'}
                        ]
                    },
                    'labelIds': []
                }
        self.mock_gmail.get_message.side_effect = get_message_side_effect

        emails = self.email_service.read_emails_headlines(max_results=2)

        expected = [
            {'id': 'msg1', 'from': 'sender1@example.com', 'subject': 'Hello', 'unread': True},
            {'id': 'msg2', 'from': 'sender2@example.com', 'subject': 'Meeting', 'unread': False}
        ]
        self.assertEqual(emails, expected)
        self.mock_gmail.list_messages.assert_called_once_with(max_results=2, query="")

    def test_read_emails_headlines_empty(self):
        self.mock_gmail.list_messages.return_value = []
        emails = self.email_service.read_emails_headlines()
        self.assertEqual(emails, [])

    # -------------------------------------------------------------------------
    # Tests for search_email_by_subject
    # -------------------------------------------------------------------------
    def test_search_email_by_subject(self):
        self.mock_gmail.list_messages.return_value = [
            {'id': 'msg1'},
            {'id': 'msg2'}
        ]
        def get_message_side_effect(msg_id):
            if msg_id == 'msg1':
                return {
                    'payload': {
                        'headers': [
                            {'name': 'From', 'value': 'alice@example.com'},
                            {'name': 'Subject', 'value': 'Invoice #123'}
                        ]
                    }
                }
            else:
                return {
                    'payload': {
                        'headers': [
                            {'name': 'From', 'value': 'bob@example.com'},
                            {'name': 'Subject', 'value': 'Invoice reminder'}
                        ]
                    }
                }
        self.mock_gmail.get_message.side_effect = get_message_side_effect

        results = self.email_service.search_email_by_subject('Invoice')
        expected = [
            {'id': 'msg1', 'from': 'alice@example.com', 'subject': 'Invoice #123'},
            {'id': 'msg2', 'from': 'bob@example.com', 'subject': 'Invoice reminder'}
        ]
        self.assertEqual(results, expected)
        self.mock_gmail.list_messages.assert_called_once_with(query='subject:Invoice', max_results=20)

    def test_search_email_by_subject_no_results(self):
        self.mock_gmail.list_messages.return_value = []
        results = self.email_service.search_email_by_subject('nonexistent')
        self.assertEqual(results, [])

if __name__ == '__main__':
    unittest.main()