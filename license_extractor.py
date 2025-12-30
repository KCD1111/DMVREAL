import re
import datetime
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LicenseExtractor:
    REQUIRED_FIELDS = ['first_name', 'last_name', 'license_number', 'date_of_birth', 'expiration_date']
    OPTIONAL_FIELDS = ['street_address', 'city', 'state', 'zip_code', 'sex']

    STATE_ABBREVIATIONS = [
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
    ]

    def __init__(self):
        pass

    def validate_and_normalize(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {}

        normalized['first_name'] = self._normalize_name(extracted_data.get('first_name'))
        normalized['last_name'] = self._normalize_name(extracted_data.get('last_name'))
        normalized['license_number'] = self._normalize_license_number(extracted_data.get('license_number'))
        normalized['date_of_birth'] = self._normalize_date(extracted_data.get('date_of_birth'))
        normalized['expiration_date'] = self._normalize_date(extracted_data.get('expiration_date'))
        normalized['street_address'] = self._normalize_address(extracted_data.get('street_address'))
        normalized['city'] = self._normalize_city(extracted_data.get('city'))
        normalized['state'] = self._normalize_state(extracted_data.get('state'))
        normalized['zip_code'] = self._normalize_zip(extracted_data.get('zip_code'))
        normalized['sex'] = self._normalize_sex(extracted_data.get('sex'))

        # Ensure confidence is always a dictionary
        confidence = extracted_data.get('confidence', {})
        if not isinstance(confidence, dict):
            confidence = {}
        normalized['confidence'] = confidence

        return normalized

    def _normalize_name(self, name):
        if not name or name == 'null':
            return None
        name_str = str(name).strip()
        # Filter out placeholder text
        placeholder_keywords = ['string', 'null', 'or', 'name']
        if any(keyword in name_str.lower() for keyword in placeholder_keywords) and len(name_str.split()) > 2:
            return None
        return name_str.title()

    def _normalize_license_number(self, license_num):
        if not license_num or license_num == 'null':
            return None
        license_str = str(license_num).strip()
        # Filter out placeholder text
        if 'string' in license_str.lower() or 'or' in license_str.lower():
            return None
        return re.sub(r'\s+', '', license_str.upper())

    def _normalize_date(self, date_str):
        if not date_str or date_str == 'null':
            return None

        date_str = str(date_str).strip()

        # Filter out placeholder text like "MM/DD/YYYY or null"
        if 'or' in date_str.lower() or date_str.upper() == 'MM/DD/YYYY' or date_str.upper() == 'DD/MM/YYYY':
            return None

        formats = [
            '%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%Y/%m/%d',
            '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%y', '%m-%d-%y',
            '%d/%m/%y', '%d-%m-%y'
        ]

        for fmt in formats:
            try:
                dt = datetime.datetime.strptime(date_str, fmt)
                if dt.year < 100:
                    dt = dt.replace(year=dt.year + 2000 if dt.year < 50 else dt.year + 1900)
                return dt.strftime('%m/%d/%Y')
            except ValueError:
                continue

        return None

    def _normalize_address(self, address):
        if not address or address == 'null':
            return None
        address_str = str(address).strip()
        # Filter out placeholder text
        if 'string' in address_str.lower() or 'or null' in address_str.lower():
            return None
        return address_str

    def _normalize_city(self, city):
        if not city or city == 'null':
            return None
        city_str = str(city).strip()
        # Filter out placeholder text
        if 'string' in city_str.lower() or 'or null' in city_str.lower():
            return None
        return city_str.title()

    def _normalize_state(self, state):
        if not state or state == 'null':
            return None
        state_str = str(state).strip().upper()
        # Filter out placeholder text
        if 'LETTER' in state_str or 'CODE' in state_str or 'OR' in state_str:
            return None
        if state_str in self.STATE_ABBREVIATIONS:
            return state_str
        return None

    def _normalize_zip(self, zip_code):
        if not zip_code or zip_code == 'null':
            return None
        zip_str = str(zip_code).strip()
        # Filter out placeholder text
        if 'string' in zip_str.lower() or 'or null' in zip_str.lower():
            return None
        zip_match = re.match(r'(\d{5})(?:-?(\d{4}))?', zip_str)
        if zip_match:
            if zip_match.group(2):
                return f"{zip_match.group(1)}-{zip_match.group(2)}"
            return zip_match.group(1)
        return None

    def _normalize_sex(self, sex):
        if not sex or sex == 'null':
            return None
        sex_str = str(sex).strip().upper()
        # Filter out placeholder text like "M OR F OR NULL"
        if 'OR' in sex_str or 'NULL' in sex_str:
            return None
        if sex_str in ['M', 'MALE']:
            return 'M'
        elif sex_str in ['F', 'FEMALE']:
            return 'F'
        return None

    def validate_data(self, normalized_data: Dict[str, Any]) -> Dict[str, List]:
        validation_report = {
            'missing_fields': [],
            'format_errors': [],
            'invalid_values': [],
            'warnings': []
        }

        for field in self.REQUIRED_FIELDS:
            value = normalized_data.get(field)
            if not value or value == 'null':
                validation_report['missing_fields'].append(field)

        if normalized_data.get('date_of_birth'):
            if not self._is_valid_date_format(normalized_data['date_of_birth']):
                validation_report['format_errors'].append({
                    'field': 'date_of_birth',
                    'value': normalized_data['date_of_birth'],
                    'error': 'Invalid date format'
                })
            else:
                try:
                    dob = datetime.datetime.strptime(normalized_data['date_of_birth'], '%m/%d/%Y')
                    age = (datetime.datetime.now() - dob).days // 365
                    if age < 16 or age > 120:
                        validation_report['warnings'].append({
                            'field': 'date_of_birth',
                            'warning': f'Unusual age: {age} years'
                        })
                except Exception:
                    pass

        if normalized_data.get('expiration_date'):
            if not self._is_valid_date_format(normalized_data['expiration_date']):
                validation_report['format_errors'].append({
                    'field': 'expiration_date',
                    'value': normalized_data['expiration_date'],
                    'error': 'Invalid date format'
                })
            else:
                try:
                    exp_date = datetime.datetime.strptime(normalized_data['expiration_date'], '%m/%d/%Y')
                    if exp_date < datetime.datetime.now():
                        validation_report['warnings'].append({
                            'field': 'expiration_date',
                            'warning': 'License is expired'
                        })
                except Exception:
                    pass

        if normalized_data.get('state'):
            if normalized_data['state'] not in self.STATE_ABBREVIATIONS:
                validation_report['invalid_values'].append({
                    'field': 'state',
                    'value': normalized_data['state'],
                    'error': 'Invalid state abbreviation'
                })

        if normalized_data.get('sex'):
            if normalized_data['sex'] not in ['M', 'F']:
                validation_report['invalid_values'].append({
                    'field': 'sex',
                    'value': normalized_data['sex'],
                    'error': 'Sex must be M or F'
                })

        confidence_scores = normalized_data.get('confidence', {})
        # Ensure confidence_scores is a dictionary before calling .items()
        if not isinstance(confidence_scores, dict):
            confidence_scores = {}
        
        for field, score in confidence_scores.items():
            if isinstance(score, (int, float)) and score < 0.7:
                validation_report['warnings'].append({
                    'field': field,
                    'warning': f'Low confidence score: {score:.2f}'
                })

        return validation_report

    def _is_valid_date_format(self, date_str):
        try:
            datetime.datetime.strptime(date_str, '%m/%d/%Y')
            return True
        except ValueError:
            return False

    def calculate_confidence_summary(self, confidence_scores: Dict[str, float]) -> float:
        if not confidence_scores or not isinstance(confidence_scores, dict):
            return 0.0

        scores = [v for v in confidence_scores.values() if isinstance(v, (int, float))]
        if not scores:
            return 0.0

        return sum(scores) / len(scores)
