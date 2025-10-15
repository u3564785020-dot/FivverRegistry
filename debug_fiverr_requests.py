#!/usr/bin/env python3
"""
Отладка HTTP запросов Fiverr
Перехватываем все запросы при регистрации
"""

import aiohttp
import asyncio
import json
import re
from urllib.parse import urljoin, urlparse

class FiverrRequestDebugger:
    def __init__(self):
        self.session = None
        self.base_url = "https://www.fiverr.com"
        self.requests_log = []
        
    async def __aenter__(self):
        await self._init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _init_session(self):
        """Инициализация сессии"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        timeout = aiohttp.ClientTimeout(total=30)
        
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
    
    async def debug_registration_flow(self):
        """Отладка процесса регистрации"""
        print("Starting registration flow debugging...")
        
        # 1. Получаем главную страницу
        print("\n1. Getting main page...")
        await self._debug_request("GET", self.base_url)
        
        # 2. Получаем страницу регистрации
        print("\n2. Getting registration page...")
        await self._debug_request("GET", f"{self.base_url}/register")
        
        # 3. Пробуем разные API эндпоинты
        print("\n3. Checking API endpoints...")
        api_endpoints = [
            f"{self.base_url}/api/v1/auth/signup",
            f"{self.base_url}/api/v2/auth/signup", 
            f"{self.base_url}/api/auth/signup",
            f"{self.base_url}/auth/signup",
            f"{self.base_url}/user/register"
        ]
        
        for endpoint in api_endpoints:
            await self._debug_request("GET", endpoint)
            await self._debug_request("POST", endpoint, {
                "email": "test@example.com",
                "username": "test_user",
                "password": "TestPassword123"
            })
        
        # 4. Ищем скрытые эндпоинты в HTML
        print("\n4. Looking for hidden endpoints...")
        await self._find_hidden_endpoints()
        
        # 5. Генерируем отчет
        print("\n5. Generating report...")
        self._generate_report()
    
    async def _debug_request(self, method: str, url: str, data: dict = None):
        """Отладка одного запроса"""
        try:
            print(f"  {method} {url}")
            
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    await self._log_request(method, url, None, response)
            else:
                headers = {'Content-Type': 'application/json'}
                async with self.session.post(url, json=data, headers=headers) as response:
                    await self._log_request(method, url, data, response)
                    
        except Exception as e:
            print(f"    ERROR: {e}")
    
    async def _log_request(self, method: str, url: str, data: dict, response):
        """Логирование запроса"""
        request_info = {
            'method': method,
            'url': url,
            'data': data,
            'status': response.status,
            'headers': dict(response.headers),
            'cookies': dict(response.cookies)
        }
        
        try:
            response_text = await response.text()
            request_info['response_text'] = response_text[:500]  # Первые 500 символов
            
            # Ищем CSRF токены в ответе
            csrf_tokens = self._extract_csrf_tokens(response_text)
            if csrf_tokens:
                request_info['csrf_tokens'] = csrf_tokens
                print(f"    CSRF tokens found: {csrf_tokens}")
            
            # Ищем формы
            forms = self._extract_forms(response_text)
            if forms:
                request_info['forms'] = forms
                print(f"    Forms found: {len(forms)}")
            
        except Exception as e:
            request_info['response_error'] = str(e)
        
        self.requests_log.append(request_info)
        print(f"    Status: {response.status}")
    
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
            r'<meta name="_token" content="([^"]+)"'
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
                'inputs': self._extract_form_inputs(form_html)
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
    
    def _extract_form_inputs(self, form_html: str):
        """Извлечение input полей"""
        inputs = []
        input_pattern = r'<input[^>]*>'
        input_matches = re.findall(input_pattern, form_html, re.IGNORECASE)
        
        for input_html in input_matches:
            input_info = {}
            attrs = ['name', 'type', 'value', 'placeholder', 'required', 'id', 'class']
            for attr in attrs:
                attr_match = re.search(f'{attr}=["\']([^"\']*)["\']', input_html, re.IGNORECASE)
                if attr_match:
                    input_info[attr] = attr_match.group(1)
            inputs.append(input_info)
        
        return inputs
    
    async def _find_hidden_endpoints(self):
        """Поиск скрытых эндпоинтов в HTML"""
        try:
            async with self.session.get(f"{self.base_url}/register") as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Ищем JavaScript файлы
                    js_files = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', html)
                    print(f"  JS files found: {len(js_files)}")
                    
                    # Ищем API эндпоинты в JS
                    api_patterns = [
                        r'["\']([^"\']*api[^"\']*)["\']',
                        r'["\']([^"\']*\/api\/[^"\']*)["\']',
                        r'["\']([^"\']*\/auth\/[^"\']*)["\']',
                        r'["\']([^"\']*\/signup[^"\']*)["\']',
                        r'["\']([^"\']*\/register[^"\']*)["\']'
                    ]
                    
                    endpoints = []
                    for pattern in api_patterns:
                        matches = re.findall(pattern, html, re.IGNORECASE)
                        for match in matches:
                            if match.startswith('/') or match.startswith('http'):
                                endpoints.append(match)
                    
                    unique_endpoints = list(set(endpoints))
                    print(f"  Endpoints found in HTML: {len(unique_endpoints)}")
                    
                    # Показываем первые 10
                    for endpoint in unique_endpoints[:10]:
                        print(f"    - {endpoint}")
                        
        except Exception as e:
            print(f"  ERROR finding endpoints: {e}")
    
    def _generate_report(self):
        """Генерация отчета"""
        print("\n" + "="*60)
        print("FIVERR REGISTRATION DEBUG REPORT")
        print("="*60)
        
        print(f"\nTotal requests: {len(self.requests_log)}")
        
        # Статистика по статусам
        statuses = {}
        for req in self.requests_log:
            status = req['status']
            statuses[status] = statuses.get(status, 0) + 1
        
        print(f"\nResponse statistics:")
        for status, count in statuses.items():
            print(f"  {status}: {count}")
        
        # CSRF токены
        csrf_found = False
        for req in self.requests_log:
            if 'csrf_tokens' in req and req['csrf_tokens']:
                csrf_found = True
                print(f"\nCSRF tokens found in {req['url']}:")
                for token in req['csrf_tokens']:
                    print(f"  - {token[:50]}...")
                break
        
        if not csrf_found:
            print(f"\nCSRF tokens NOT found!")
        
        # Формы
        forms_found = False
        for req in self.requests_log:
            if 'forms' in req and req['forms']:
                forms_found = True
                print(f"\nForms found in {req['url']}:")
                for i, form in enumerate(req['forms']):
                    print(f"  Form {i+1}:")
                    print(f"    Action: {form['action']}")
                    print(f"    Method: {form['method']}")
                    print(f"    Inputs: {len(form['inputs'])}")
                break
        
        if not forms_found:
            print(f"\nForms NOT found!")
        
        # Рекомендации
        print(f"\nRECOMMENDATIONS:")
        print(f"  1. Check real requests in browser DevTools")
        print(f"  2. Find correct registration endpoint")
        print(f"  3. Get real CSRF tokens")
        print(f"  4. Study POST data structure")
        
        # Сохраняем лог в файл
        with open('fiverr_debug_log.json', 'w', encoding='utf-8') as f:
            json.dump(self.requests_log, f, indent=2, ensure_ascii=False)
        print(f"\nLog saved to: fiverr_debug_log.json")

async def main():
    """Основная функция"""
    print("Starting Fiverr HTTP requests debugging...")
    
    async with FiverrRequestDebugger() as debugger:
        await debugger.debug_registration_flow()

if __name__ == "__main__":
    asyncio.run(main())