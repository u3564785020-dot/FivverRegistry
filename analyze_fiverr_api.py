#!/usr/bin/env python3
"""
Анализ Fiverr API для регистрации аккаунтов
Исследуем все эндпоинты, headers, CSRF токены
"""

import requests
import json
import re
from urllib.parse import urljoin, urlparse
import time

class FiverrAPIAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.fiverr.com"
        self.api_endpoints = []
        
        # Headers для имитации браузера
        self.session.headers.update({
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
        })
    
    def analyze_main_page(self):
        """Анализ главной страницы Fiverr"""
        print("Analyzing main page...")
        
        try:
            response = self.session.get(self.base_url)
            print(f"Status: {response.status_code}")
            
            # Ищем CSRF токены
            csrf_tokens = self.extract_csrf_tokens(response.text)
            if csrf_tokens:
                print(f"Found CSRF tokens: {csrf_tokens}")
            
            # Ищем API эндпоинты
            api_endpoints = self.extract_api_endpoints(response.text)
            if api_endpoints:
                print(f"Found API endpoints: {api_endpoints}")
                self.api_endpoints.extend(api_endpoints)
            
            # Ищем формы регистрации
            forms = self.extract_forms(response.text)
            if forms:
                print(f"Found forms: {len(forms)}")
            
            return response
            
        except Exception as e:
            print(f"Error analyzing main page: {e}")
            return None
    
    def analyze_registration_page(self):
        """Анализ страницы регистрации"""
        print("\nAnalyzing registration page...")
        
        registration_urls = [
            f"{self.base_url}/signup",
            f"{self.base_url}/register",
            f"{self.base_url}/join",
            f"{self.base_url}/sign_up"
        ]
        
        for url in registration_urls:
            try:
                print(f"Checking: {url}")
                response = self.session.get(url)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    # Ищем формы регистрации
                    forms = self.extract_forms(response.text)
                    if forms:
                        print(f"Found registration forms: {len(forms)}")
                    
                    # Ищем API эндпоинты
                    api_endpoints = self.extract_api_endpoints(response.text)
                    if api_endpoints:
                        print(f"API endpoints: {api_endpoints}")
                        self.api_endpoints.extend(api_endpoints)
                    
                    return response
                    
            except Exception as e:
                print(f"Error for {url}: {e}")
                continue
        
        return None
    
    def extract_csrf_tokens(self, html_content):
        """Извлечение CSRF токенов из HTML"""
        tokens = []
        
        # Ищем различные паттерны CSRF токенов
        patterns = [
            r'name="csrf_token"\s+value="([^"]+)"',
            r'name="_token"\s+value="([^"]+)"',
            r'name="authenticity_token"\s+value="([^"]+)"',
            r'"csrf_token":"([^"]+)"',
            r'"csrfToken":"([^"]+)"',
            r'"authenticity_token":"([^"]+)"',
            r'window\.csrf_token\s*=\s*["\']([^"\']+)["\']',
            r'window\._token\s*=\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            tokens.extend(matches)
        
        return list(set(tokens))  # Убираем дубликаты
    
    def extract_api_endpoints(self, html_content):
        """Извлечение API эндпоинтов из HTML/JS"""
        endpoints = []
        
        # Ищем различные паттерны API эндпоинтов
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
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if match.startswith('/') or match.startswith('http'):
                    endpoints.append(match)
        
        return list(set(endpoints))
    
    def extract_forms(self, html_content):
        """Извлечение форм из HTML"""
        forms = []
        
        # Ищем формы с помощью regex
        form_pattern = r'<form[^>]*>(.*?)</form>'
        form_matches = re.findall(form_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for i, form_html in enumerate(form_matches):
            form_info = {
                'index': i,
                'action': self.extract_form_action(form_html),
                'method': self.extract_form_method(form_html),
                'inputs': self.extract_form_inputs(form_html)
            }
            forms.append(form_info)
        
        return forms
    
    def extract_form_action(self, form_html):
        """Извлечение action формы"""
        action_match = re.search(r'action=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
        return action_match.group(1) if action_match else None
    
    def extract_form_method(self, form_html):
        """Извлечение method формы"""
        method_match = re.search(r'method=["\']([^"\']*)["\']', form_html, re.IGNORECASE)
        return method_match.group(1).upper() if method_match else 'GET'
    
    def extract_form_inputs(self, form_html):
        """Извлечение input полей формы"""
        inputs = []
        
        input_pattern = r'<input[^>]*>'
        input_matches = re.findall(input_pattern, form_html, re.IGNORECASE)
        
        for input_html in input_matches:
            input_info = {}
            
            # Извлекаем атрибуты
            attrs = ['name', 'type', 'value', 'placeholder', 'required', 'id', 'class']
            for attr in attrs:
                attr_match = re.search(f'{attr}=["\']([^"\']*)["\']', input_html, re.IGNORECASE)
                if attr_match:
                    input_info[attr] = attr_match.group(1)
            
            inputs.append(input_info)
        
        return inputs
    
    def analyze_network_requests(self):
        """Анализ сетевых запросов (имитация)"""
        print("\nAnalyzing possible network requests...")
        
        # Популярные эндпоинты для регистрации
        common_endpoints = [
            '/api/v1/auth/signup',
            '/api/v1/user/register',
            '/api/v1/auth/register',
            '/api/v2/auth/signup',
            '/api/v2/user/register',
            '/api/auth/signup',
            '/api/user/register',
            '/auth/signup',
            '/user/register',
            '/signup',
            '/register'
        ]
        
        for endpoint in common_endpoints:
            url = urljoin(self.base_url, endpoint)
            try:
                print(f"Checking: {url}")
                response = self.session.get(url)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"Content: {response.text[:200]}...")
                    
            except Exception as e:
                print(f"Error for {url}: {e}")
    
    def generate_report(self):
        """Генерация отчета"""
        print("\n" + "="*50)
        print("FIVERR API ANALYSIS REPORT")
        print("="*50)
        
        print(f"\nFound API endpoints: {len(self.api_endpoints)}")
        for endpoint in self.api_endpoints:
            print(f"  - {endpoint}")
        
        print(f"\nRecommendations:")
        print(f"  1. Use aiohttp for async requests")
        print(f"  2. Handle CSRF tokens")
        print(f"  3. Imitate browser headers")
        print(f"  4. Use sessions for cookies")
        print(f"  5. Handle captcha via API services")

def main():
    """Основная функция"""
    print("Starting Fiverr API analysis...")
    
    analyzer = FiverrAPIAnalyzer()
    
    # Анализируем главную страницу
    analyzer.analyze_main_page()
    
    # Анализируем страницу регистрации
    analyzer.analyze_registration_page()
    
    # Анализируем сетевые запросы
    analyzer.analyze_network_requests()
    
    # Генерируем отчет
    analyzer.generate_report()

if __name__ == "__main__":
    main()