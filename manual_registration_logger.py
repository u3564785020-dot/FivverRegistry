#!/usr/bin/env python3
"""
МАКСИМАЛЬНО ДЕТАЛЬНЫЙ ЛОГГЕР РУЧНОЙ РЕГИСТРАЦИИ FIVERR
Логирует ВСЕ данные для создания рабочего кода
"""

import aiohttp
import asyncio
import json
import re
import time
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime
import base64

class ManualRegistrationLogger:
    def __init__(self):
        self.session = None
        self.base_url = "https://www.fiverr.com"
        self.log_data = {
            'timestamp': datetime.now().isoformat(),
            'requests': [],
            'csrf_tokens': [],
            'forms': [],
            'cookies': {},
            'headers': {},
            'endpoints': [],
            'registration_flow': []
        }
        
    async def __aenter__(self):
        await self._init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        self._save_log()
    
    async def _init_session(self):
        """Инициализация сессии"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        timeout = aiohttp.ClientTimeout(total=60)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self._get_headers()
        )
    
    def _get_headers(self):
        """Headers для имитации браузера"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
    
    async def log_complete_registration_flow(self):
        """Логирование полного процесса регистрации"""
        print("="*80)
        print("MANUAL FIVERR REGISTRATION LOGGER")
        print("="*80)
        print("This script will log EVERYTHING needed to create working registration code")
        print("Follow the steps and I'll capture all the data!")
        print("="*80)
        
        # Шаг 1: Главная страница
        print("\n1. Getting main page...")
        await self._log_request("GET", self.base_url, "Main page")
        
        # Шаг 2: Страница регистрации
        print("\n2. Getting registration page...")
        await self._log_request("GET", f"{self.base_url}/register", "Registration page")
        
        # Шаг 3: Альтернативные страницы регистрации
        print("\n3. Getting alternative registration pages...")
        alt_pages = [
            f"{self.base_url}/auth/signup",
            f"{self.base_url}/user/register",
            f"{self.base_url}/signup"
        ]
        
        for page in alt_pages:
            await self._log_request("GET", page, f"Alternative page: {page}")
        
        # Шаг 4: Поиск всех форм
        print("\n4. Analyzing all forms...")
        await self._analyze_forms()
        
        # Шаг 5: Поиск всех API эндпоинтов
        print("\n5. Finding all API endpoints...")
        await self._find_api_endpoints()
        
        # Шаг 6: Тестирование регистрации
        print("\n6. Testing registration endpoints...")
        await self._test_registration_endpoints()
        
        # Шаг 7: Генерация отчета
        print("\n7. Generating detailed report...")
        self._generate_detailed_report()
    
    async def _log_request(self, method: str, url: str, description: str):
        """Детальное логирование запроса"""
        try:
            print(f"  {method} {url}")
            print(f"  Description: {description}")
            
            start_time = time.time()
            
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    await self._capture_request_data(method, url, None, response, description, start_time)
            else:
                async with self.session.post(url) as response:
                    await self._capture_request_data(method, url, None, response, description, start_time)
                    
        except Exception as e:
            print(f"    ERROR: {e}")
            self.log_data['requests'].append({
                'method': method,
                'url': url,
                'description': description,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    async def _capture_request_data(self, method: str, url: str, data: dict, response, description: str, start_time: float):
        """Захват всех данных запроса"""
        request_data = {
            'method': method,
            'url': url,
            'description': description,
            'timestamp': datetime.now().isoformat(),
            'duration': time.time() - start_time,
            'status': response.status,
            'request_headers': dict(response.request_info.headers),
            'response_headers': dict(response.headers),
            'cookies': dict(response.cookies),
            'url_parsed': {
                'scheme': urlparse(url).scheme,
                'netloc': urlparse(url).netloc,
                'path': urlparse(url).path,
                'query': urlparse(url).query,
                'fragment': urlparse(url).fragment
            }
        }
        
        try:
            response_text = await response.text()
            request_data['response_text'] = response_text
            request_data['response_length'] = len(response_text)
            
            # Ищем CSRF токены
            csrf_tokens = self._extract_csrf_tokens(response_text)
            if csrf_tokens:
                request_data['csrf_tokens'] = csrf_tokens
                self.log_data['csrf_tokens'].extend(csrf_tokens)
                print(f"    CSRF tokens found: {len(csrf_tokens)}")
                for token in csrf_tokens:
                    print(f"      - {token[:50]}...")
            
            # Ищем формы
            forms = self._extract_forms(response_text)
            if forms:
                request_data['forms'] = forms
                self.log_data['forms'].extend(forms)
                print(f"    Forms found: {len(forms)}")
                for i, form in enumerate(forms):
                    print(f"      Form {i+1}: {form['method']} -> {form['action']}")
                    print(f"        Inputs: {len(form['inputs'])}")
            
            # Ищем JavaScript
            js_files = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', response_text)
            if js_files:
                request_data['js_files'] = js_files
                print(f"    JS files: {len(js_files)}")
            
            # Ищем API эндпоинты
            endpoints = self._extract_endpoints(response_text)
            if endpoints:
                request_data['endpoints'] = endpoints
                self.log_data['endpoints'].extend(endpoints)
                print(f"    API endpoints: {len(endpoints)}")
            
            # Ищем скрытые поля
            hidden_fields = self._extract_hidden_fields(response_text)
            if hidden_fields:
                request_data['hidden_fields'] = hidden_fields
                print(f"    Hidden fields: {len(hidden_fields)}")
            
            # Ищем мета теги
            meta_tags = self._extract_meta_tags(response_text)
            if meta_tags:
                request_data['meta_tags'] = meta_tags
                print(f"    Meta tags: {len(meta_tags)}")
            
        except Exception as e:
            request_data['response_error'] = str(e)
            print(f"    Response error: {e}")
        
        # Сохраняем cookies
        try:
            for cookie in response.cookies:
                self.log_data['cookies'][cookie.key] = cookie.value
        except Exception as e:
            print(f"    Cookie error: {e}")
        
        self.log_data['requests'].append(request_data)
        print(f"    Status: {response.status}")
        print(f"    Duration: {request_data['duration']:.2f}s")
    
    def _extract_csrf_tokens(self, html: str):
        """Извлечение CSRF токенов"""
        tokens = []
        patterns = [
            r'name="csrf_token"\s+value="([^"]+)"',
            r'name="_token"\s+value="([^"]+)"',
            r'name="authenticity_token"\s+value="([^"]+)"',
            r'"csrf_token":"([^"]+)"',
            r'"csrfToken":"([^"]+)"',
            r'"authenticity_token":"([^"]+)"',
            r'window\.csrf_token\s*=\s*["\']([^"\']+)["\']',
            r'window\._token\s*=\s*["\']([^"\']+)["\']',
            r'<meta name="csrf-token" content="([^"]+)"',
            r'<meta name="_token" content="([^"]+)"',
            r'<input[^>]*name=["\']_token["\'][^>]*value=["\']([^"]+)["\']',
            r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"]+)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            tokens.extend(matches)
        
        return list(set(tokens))
    
    def _extract_forms(self, html: str):
        """Извлечение форм"""
        forms = []
        form_pattern = r'<form[^>]*>(.*?)</form>'
        form_matches = re.findall(form_pattern, html, re.DOTALL | re.IGNORECASE)
        
        for i, form_html in enumerate(form_matches):
            form_info = {
                'index': i,
                'action': self._extract_form_action(form_html),
                'method': self._extract_form_method(form_html),
                'enctype': self._extract_form_enctype(form_html),
                'inputs': self._extract_form_inputs(form_html),
                'raw_html': form_html[:500]  # Первые 500 символов
            }
            forms.append(form_info)
        
        return forms
    
    def _extract_form_action(self, form_html: str):
        """Извлечение action формы"""
        action_match = re.search(r'action=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
        return action_match.group(1) if action_match else None
    
    def _extract_form_method(self, form_html: str):
        """Извлечение method формы"""
        method_match = re.search(r'method=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
        return method_match.group(1).upper() if method_match else 'GET'
    
    def _extract_form_enctype(self, form_html: str):
        """Извлечение enctype формы"""
        enctype_match = re.search(r'enctype=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
        return enctype_match.group(1) if enctype_match else 'application/x-www-form-urlencoded'
    
    def _extract_form_inputs(self, form_html: str):
        """Извлечение input полей"""
        inputs = []
        input_pattern = r'<input[^>]*>'
        input_matches = re.findall(input_pattern, form_html, re.IGNORECASE)
        
        for input_html in input_matches:
            input_info = {}
            attrs = ['name', 'type', 'value', 'placeholder', 'required', 'id', 'class', 'data-*']
            for attr in attrs:
                if attr == 'data-*':
                    # Ищем все data- атрибуты
                    data_attrs = re.findall(r'data-([^=]+)=["\']([^"\']*)["\']', input_html, re.IGNORECASE)
                    if data_attrs:
                        input_info['data_attributes'] = dict(data_attrs)
                else:
                    attr_match = re.search(f'{attr}=["\']([^"\']*)["\']', input_html, re.IGNORECASE)
                    if attr_match:
                        input_info[attr] = attr_match.group(1)
            
            input_info['raw_html'] = input_html
            inputs.append(input_info)
        
        return inputs
    
    def _extract_endpoints(self, html: str):
        """Извлечение API эндпоинтов"""
        endpoints = []
        patterns = [
            r'["\']([^"\']*api[^"\']*)["\']',
            r'["\']([^"\']*\/api\/[^"\']*)["\']',
            r'["\']([^"\']*\/v\d+\/[^"\']*)["\']',
            r'["\']([^"\']*\/auth\/[^"\']*)["\']',
            r'["\']([^"\']*\/signup[^"\']*)["\']',
            r'["\']([^"\']*\/register[^"\']*)["\']',
            r'["\']([^"\']*\/user[^"\']*)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if match.startswith('/') or match.startswith('http'):
                    endpoints.append(match)
        
        return list(set(endpoints))
    
    def _extract_hidden_fields(self, html: str):
        """Извлечение скрытых полей"""
        hidden_fields = []
        hidden_pattern = r'<input[^>]*type=["\']hidden["\'][^>]*>'
        hidden_matches = re.findall(hidden_pattern, html, re.IGNORECASE)
        
        for hidden_html in hidden_matches:
            field_info = {}
            attrs = ['name', 'value', 'id']
            for attr in attrs:
                attr_match = re.search(f'{attr}=["\']([^"\']*)["\']', hidden_html, re.IGNORECASE)
                if attr_match:
                    field_info[attr] = attr_match.group(1)
            field_info['raw_html'] = hidden_html
            hidden_fields.append(field_info)
        
        return hidden_fields
    
    def _extract_meta_tags(self, html: str):
        """Извлечение мета тегов"""
        meta_tags = []
        meta_pattern = r'<meta[^>]*>'
        meta_matches = re.findall(meta_pattern, html, re.IGNORECASE)
        
        for meta_html in meta_matches:
            meta_info = {}
            attrs = ['name', 'content', 'property', 'http-equiv']
            for attr in attrs:
                attr_match = re.search(f'{attr}=["\']([^"\']*)["\']', meta_html, re.IGNORECASE)
                if attr_match:
                    meta_info[attr] = attr_match.group(1)
            meta_info['raw_html'] = meta_html
            meta_tags.append(meta_info)
        
        return meta_tags
    
    async def _analyze_forms(self):
        """Анализ всех найденных форм"""
        print("  Analyzing all forms...")
        
        for request in self.log_data['requests']:
            if 'forms' in request and request['forms']:
                print(f"    Forms in {request['url']}:")
                for i, form in enumerate(request['forms']):
                    print(f"      Form {i+1}:")
                    print(f"        Action: {form['action']}")
                    print(f"        Method: {form['method']}")
                    print(f"        Enctype: {form['enctype']}")
                    print(f"        Inputs: {len(form['inputs'])}")
                    
                    # Анализируем поля
                    for j, input_field in enumerate(form['inputs']):
                        if input_field.get('name'):
                            print(f"          Input {j+1}: {input_field['name']} ({input_field.get('type', 'text')})")
    
    async def _find_api_endpoints(self):
        """Поиск всех API эндпоинтов"""
        print("  Finding all API endpoints...")
        
        all_endpoints = set()
        for request in self.log_data['requests']:
            if 'endpoints' in request:
                all_endpoints.update(request['endpoints'])
        
        print(f"    Total unique endpoints found: {len(all_endpoints)}")
        
        # Группируем по типам
        auth_endpoints = [ep for ep in all_endpoints if 'auth' in ep.lower()]
        user_endpoints = [ep for ep in all_endpoints if 'user' in ep.lower()]
        signup_endpoints = [ep for ep in all_endpoints if 'signup' in ep.lower() or 'register' in ep.lower()]
        
        print(f"    Auth endpoints: {len(auth_endpoints)}")
        print(f"    User endpoints: {len(user_endpoints)}")
        print(f"    Signup endpoints: {len(signup_endpoints)}")
        
        # Показываем самые важные
        important_endpoints = auth_endpoints + signup_endpoints
        for endpoint in important_endpoints[:10]:
            print(f"      - {endpoint}")
    
    async def _test_registration_endpoints(self):
        """Тестирование эндпоинтов регистрации"""
        print("  Testing registration endpoints...")
        
        test_data = {
            "email": "test@example.com",
            "username": "test_user_123",
            "password": "TestPassword123!",
            "password_confirmation": "TestPassword123!",
            "terms": True,
            "privacy": True
        }
        
        # Находим все эндпоинты связанные с регистрацией
        registration_endpoints = []
        for request in self.log_data['requests']:
            if 'endpoints' in request:
                for endpoint in request['endpoints']:
                    if any(keyword in endpoint.lower() for keyword in ['signup', 'register', 'auth']):
                        full_url = urljoin(self.base_url, endpoint)
                        registration_endpoints.append(full_url)
        
        # Тестируем каждый эндпоинт
        for endpoint in registration_endpoints[:5]:  # Тестируем первые 5
            try:
                print(f"    Testing: {endpoint}")
                
                # GET запрос
                async with self.session.get(endpoint) as response:
                    print(f"      GET {response.status}")
                
                # POST запрос с JSON
                headers = {'Content-Type': 'application/json'}
                async with self.session.post(endpoint, json=test_data, headers=headers) as response:
                    print(f"      POST JSON {response.status}")
                    if response.status != 404:
                        response_text = await response.text()
                        print(f"        Response: {response_text[:100]}...")
                
                # POST запрос с form-data
                form_data = aiohttp.FormData()
                for key, value in test_data.items():
                    form_data.add_field(key, str(value))
                
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                async with self.session.post(endpoint, data=form_data, headers=headers) as response:
                    print(f"      POST FORM {response.status}")
                    if response.status != 404:
                        response_text = await response.text()
                        print(f"        Response: {response_text[:100]}...")
                        
            except Exception as e:
                print(f"      ERROR: {e}")
    
    def _generate_detailed_report(self):
        """Генерация детального отчета"""
        print("\n" + "="*80)
        print("DETAILED REGISTRATION ANALYSIS REPORT")
        print("="*80)
        
        print(f"\nTotal requests logged: {len(self.log_data['requests'])}")
        print(f"CSRF tokens found: {len(self.log_data['csrf_tokens'])}")
        print(f"Forms found: {len(self.log_data['forms'])}")
        print(f"API endpoints found: {len(self.log_data['endpoints'])}")
        print(f"Cookies collected: {len(self.log_data['cookies'])}")
        
        # Статистика по статусам
        statuses = {}
        for req in self.log_data['requests']:
            if 'status' in req:
                status = req['status']
                statuses[status] = statuses.get(status, 0) + 1
        
        print(f"\nResponse status statistics:")
        for status, count in statuses.items():
            print(f"  {status}: {count}")
        
        # CSRF токены
        if self.log_data['csrf_tokens']:
            print(f"\nCSRF Tokens found:")
            for i, token in enumerate(self.log_data['csrf_tokens']):
                print(f"  {i+1}. {token}")
        
        # Формы регистрации
        registration_forms = []
        for form in self.log_data['forms']:
            if form['action'] and any(keyword in form['action'].lower() for keyword in ['signup', 'register', 'auth']):
                registration_forms.append(form)
        
        if registration_forms:
            print(f"\nRegistration forms found: {len(registration_forms)}")
            for i, form in enumerate(registration_forms):
                print(f"  Form {i+1}:")
                print(f"    Action: {form['action']}")
                print(f"    Method: {form['method']}")
                print(f"    Enctype: {form['enctype']}")
                print(f"    Inputs: {len(form['inputs'])}")
        
        # Рекомендации для кода
        print(f"\nCODE GENERATION RECOMMENDATIONS:")
        print(f"  1. Use these CSRF tokens: {self.log_data['csrf_tokens'][:3]}")
        print(f"  2. Try these endpoints first:")
        for endpoint in self.log_data['endpoints'][:5]:
            if any(keyword in endpoint.lower() for keyword in ['signup', 'register', 'auth']):
                print(f"     - {endpoint}")
        print(f"  3. Use these headers:")
        print(f"     - User-Agent: {self._get_headers()['User-Agent']}")
        print(f"     - Accept: {self._get_headers()['Accept']}")
        print(f"  4. Include these cookies: {list(self.log_data['cookies'].keys())}")
        
        print(f"\n" + "="*80)
        print("LOG SAVED TO: manual_registration_log.json")
        print("Use this data to create working registration code!")
        print("="*80)
    
    def _save_log(self):
        """Сохранение лога"""
        with open('manual_registration_log.json', 'w', encoding='utf-8') as f:
            json.dump(self.log_data, f, indent=2, ensure_ascii=False)

async def main():
    """Основная функция"""
    print("Starting manual registration logger...")
    print("This will capture ALL data needed for registration!")
    
    async with ManualRegistrationLogger() as logger:
        await logger.log_complete_registration_flow()

if __name__ == "__main__":
    asyncio.run(main())
