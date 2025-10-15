"""
BrightData API Service для обхода капчи
Использует BrightData Unlocker для автоматического обхода PerimeterX и других капч
"""

import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any
from utils.logger import logger


class BrightDataAPIService:
    """Сервис для работы с BrightData API"""
    
    def __init__(self, api_key: str = "22200941061de75cc98202b395c45e754cb4ee077ab9fcf596a17df27151e9b6"):
        self.api_key = api_key
        self.base_url = "https://api.brightdata.com"
        self.zone = "web_unlocker2"
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение HTTP сессии"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Закрытие сессии"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def unlock_url(self, url: str, format: str = "raw") -> Optional[Dict[str, Any]]:
        """
        Разблокировка URL через BrightData Unlocker
        
        Args:
            url: URL для разблокировки
            format: Формат ответа (raw, html, json)
            
        Returns:
            Словарь с результатом разблокировки
        """
        try:
            session = await self._get_session()
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "zone": self.zone,
                "url": url,
                "format": format
            }
            
            logger.info(f"🔓 Запрос к BrightData для разблокировки: {url}")
            
            async with session.post(
                f"{self.base_url}/request",
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    result = await response.text()
                    logger.info(f"✅ BrightData успешно разблокировал URL")
                    
                    return {
                        "success": True,
                        "data": result,
                        "status_code": response.status,
                        "headers": dict(response.headers)
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка BrightData: {response.status} - {error_text}")
                    
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "status_code": response.status
                    }
                    
        except asyncio.TimeoutError:
            logger.error("⏰ Таймаут при запросе к BrightData")
            return {
                "success": False,
                "error": "Таймаут при запросе к BrightData"
            }
        except Exception as e:
            logger.error(f"❌ Ошибка BrightData API: {e}")
            return {
                "success": False,
                "error": f"Ошибка API: {str(e)}"
            }
    
    async def get_proxy_config(self) -> Optional[Dict[str, str]]:
        """
        Получение конфигурации прокси для BrightData
        
        Returns:
            Словарь с настройками прокси
        """
        try:
            # Тестовый запрос для получения прокси
            test_url = "https://geo.brdtest.com/welcome.txt?product=unlocker&method=api"
            result = await self.unlock_url(test_url)
            
            if result and result.get("success"):
                # BrightData автоматически предоставляет прокси через API
                # Возвращаем конфигурацию для использования в Playwright
                return {
                    "server": f"http://{self.zone}.brightdata.com:22225",
                    "username": f"brd-customer-hl_{self.api_key[:8]}",
                    "password": self.api_key
                }
            else:
                logger.error("❌ Не удалось получить конфигурацию прокси BrightData")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения прокси конфигурации: {e}")
            return None
    
    async def unlock_fiverr_page(self, page_url: str = "https://it.fiverr.com/") -> Optional[str]:
        """
        Разблокировка страницы Fiverr через BrightData
        
        Args:
            page_url: URL страницы Fiverr
            
        Returns:
            HTML содержимое разблокированной страницы
        """
        try:
            logger.info(f"🔓 Разблокируем страницу Fiverr через BrightData...")
            
            result = await self.unlock_url(page_url, format="html")
            
            if result and result.get("success"):
                html_content = result.get("data", "")
                logger.info(f"✅ Страница Fiverr успешно разблокирована (размер: {len(html_content)} символов)")
                return html_content
            else:
                logger.error(f"❌ Не удалось разблокировать страницу Fiverr: {result.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка разблокировки страницы Fiverr: {e}")
            return None
    
    async def check_captcha_bypass(self, page_url: str = "https://it.fiverr.com/") -> bool:
        """
        Проверка обхода капчи на странице
        
        Args:
            page_url: URL для проверки
            
        Returns:
            True если капча обойдена, False если нет
        """
        try:
            logger.info(f"🔍 Проверяем обход капчи на {page_url}...")
            
            result = await self.unlock_url(page_url, format="html")
            
            if result and result.get("success"):
                html_content = result.get("data", "")
                
                # Проверяем наличие капчи в HTML
                captcha_indicators = [
                    "px-captcha",
                    "PRESS",
                    "HOLD", 
                    "captcha",
                    "recaptcha",
                    "hcaptcha",
                    "cloudflare"
                ]
                
                captcha_found = any(indicator.lower() in html_content.lower() for indicator in captcha_indicators)
                
                if not captcha_found:
                    logger.info("✅ Капча успешно обойдена через BrightData!")
                    return True
                else:
                    logger.warning("⚠️ Капча все еще присутствует на странице")
                    return False
            else:
                logger.error(f"❌ Не удалось проверить обход капчи: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки обхода капчи: {e}")
            return False
