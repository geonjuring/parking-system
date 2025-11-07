# gradio_parking_app.py
"""
주차장 관리 시스템 - Gradio 웹 인터페이스

기존 main.py와 parking_classes.py의 기능을 Gradio로 구현한 웹 애플리케이션
지도 표시 기능 포함 (OpenStreetMap + Leaflet.js)
"""

import gradio as gr
import time
import logging
import sys
import json
import os
import urllib.parse
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import random
import requests

# parking_classes.py에서 클래스들을 가져옵니다
from parking_classes import ParkingLot, ParkingManager

# 사용자 인증 시스템 가져오기
from user_auth import UserAuthSystem

# 공통 데이터 파일에서 주차장 데이터를 가져옵니다.
from parking_data import get_dongs_data
from parking_fee_calculator import calculate_fee_with_thinking, calculate_current_fee, format_fee_result, get_parking_duration_info, calculate_estimated_fee, format_estimated_fee_result

# ==================== 설정 ====================
# 로깅 설정
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ==================== 전역 변수 ====================
# 시스템 관리자 (전역으로 관리)
manager: Optional[ParkingManager] = None

# 사용자 인증 시스템 (전역으로 관리)
auth_system: Optional[UserAuthSystem] = None

# ==================== 로깅 설정 ====================
def setup_logging() -> None:
    """로깅 시스템을 설정합니다."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[logging.FileHandler('parking_system.log', encoding='utf-8')]
    )
    logger = logging.getLogger(__name__)
    logger.info("주차장 관리 시스템 (Gradio) 시작")

# ==================== 시스템 초기화 ====================
def initialize_system() -> ParkingManager:
    """주차장 관리 시스템을 초기화합니다."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("시스템 초기화 시작")
        manager = ParkingManager()
        logger.info("시스템 초기화 완료")
        return manager
    except Exception as e:
        logger.error(f"시스템 초기화 실패: {e}")
        raise

# ==================== 데이터 설정 ====================
def setup_parking_data(manager: ParkingManager) -> bool:
    """주차장 데이터를 설정합니다."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("주차장 데이터 설정 시작")
        
        # 공통 데이터 파일에서 주차장 데이터 가져오기
        dongs_data = get_dongs_data()
        
        for dong_name, lots_data in dongs_data:
            # 동 추가
            if not manager.add_dong(dong_name):
                logger.error(f"동 '{dong_name}' 추가 실패")
                return False
                
            # 동 객체 가져오기
            dong = manager.get_dong(dong_name)
            if not dong:
                logger.error(f"동 '{dong_name}' 조회 실패")
                return False
            
            # 주차장 추가
            for lot_name, total_spaces, address, parking_type, price_info, charger_info in lots_data:
                try:
                    lot = ParkingLot(lot_name, total_spaces, address, parking_type, price_info)
                    if not dong.add_lot(lot):
                        logger.error(f"주차장 '{lot_name}' 추가 실패")
                        return False
                except Exception as e:
                    logger.error(f"주차장 '{lot_name}' 생성 실패: {e}")
                    return False
        
        logger.info("주차장 데이터 설정 완료")
        return True
        
    except Exception as e:
        logger.error(f"주차장 데이터 설정 실패: {e}")
        return False

# ==================== Gradio 인터페이스 함수들 ====================
def get_dong_list() -> List[str]:
    """등록된 동 목록을 반환합니다."""
    global manager
    if not manager:
        return []
    return manager.get_dong_names()

def get_parking_lots(dong_name: str) -> List[str]:
    """선택된 동의 주차장 목록을 반환합니다."""
    global manager
    if not manager or not dong_name:
        return []
    
    dong = manager.get_dong(dong_name)
    if not dong:
        return []
    
    return dong.get_lot_names()

def get_parking_status(dong_name: str) -> str:
    """선택된 동의 주차장 현황을 반환합니다."""
    global manager
    if not manager or not dong_name:
        return "❌ 동을 선택해주세요."
    
    dong = manager.get_dong(dong_name)
    if not dong:
        return f"❌ '{dong_name}' 동을 찾을 수 없습니다."
    
    # 전기차 충전소 정보 가져오기
    from parking_data import get_ev_charger_info
    
    # 동 현황 헤더
    result = f"🏘️ **{dong.name} 주차장 현황**\n"
    result += "=" * 50 + "\n\n"
    
    lot_names = dong.get_lot_names()
    if not lot_names:
        result += "❌ 등록된 주차장이 없습니다."
        return result
    
    # 모든 주차장 현황 표시
    for lot_name in lot_names:
        lot = dong.get_lot_by_name(lot_name)
        if lot:
            occupancy_rate = lot.get_occupancy_rate()
            available_spaces = lot.get_available_spaces()
            
            # 혼잡도 상태 아이콘 및 텍스트
            if occupancy_rate >= 0.9:
                status_icon = "🔴"
                status_text = "매우 혼잡"
            elif occupancy_rate >= 0.7:
                status_icon = "🟠"
                status_text = "혼잡"
            elif occupancy_rate >= 0.4:
                status_icon = "🟡"
                status_text = "보통"
            else:
                status_icon = "🟢"
                status_text = "여유"
            
            # 전기차 충전소 정보 먼저 확인
            charger_info = get_ev_charger_info(lot_name)
            has_charger = charger_info and charger_info.get('has_charger')
            
            # 유형에 따른 시각적 구분 (전기차 충전소 아이콘 추가)
            charger_icon = "🔌" if has_charger else ""
            if lot.parking_type == "유료":
                result += f"🔴 **[유료] {charger_icon} {lot.name}**\n"
            else:
                result += f"🟢 **[무료] {charger_icon} {lot.name}**\n"
            
            result += f"📍 주소: {lot.location_info}\n"
            result += f"🚗 현재: {lot.current_cars}/{lot.total_spaces} ({occupancy_rate:.1%})\n"
            result += f"🆓 여유: {available_spaces}개\n"
            result += f"💰 유형: {lot.parking_type}\n"
            result += f"💵 가격: {lot.price_info}\n"
            
            # 전기차 충전소 정보 표시
            if has_charger:
                chargers = charger_info.get('chargers', [])
                fast_count = sum(1 for c in chargers if c['charge_type'] == '급속')
                slow_count = sum(1 for c in chargers if c['charge_type'] == '완속')
                available_count = sum(1 for c in chargers if c['is_available'])
                result += f"🔌 **전기차 충전소**: ✅ **있음** (급속 {fast_count}개, 완속 {slow_count}개, 이용가능 {available_count}개)\n"
            else:
                result += f"🔌 **전기차 충전소**: ❌ 없음\n"
            result += f"{status_icon} **혼잡도**: {status_text}\n"
            
            # 시각적 표시
            visual_bar = '█' * int(occupancy_rate * 15) + '░' * (15 - int(occupancy_rate * 15))
            result += f"📊 {visual_bar} {occupancy_rate:.1%}\n\n"
    
    return result

def get_lot_detail(dong_name: str, lot_name: str) -> str:
    """선택된 주차장의 상세 정보를 반환합니다."""
    global manager
    if not manager or not dong_name or not lot_name:
        return "❌ 동과 주차장을 선택해주세요."
    
    dong = manager.get_dong(dong_name)
    if not dong:
        return f"❌ '{dong_name}' 동을 찾을 수 없습니다."
    
    lot = dong.get_lot_by_name(lot_name)
    if not lot:
        return f"❌ '{lot_name}' 주차장을 찾을 수 없습니다."
    
    # 전기차 충전소 정보 가져오기
    from parking_data import get_ev_charger_info
    
    # 주차장 상세 정보
    result = f"🅿️ **{lot.name} 상세 정보**\n"
    result += "=" * 50 + "\n\n"
    
    # 기본 정보
    result += f"📍 **주소**: {lot.location_info}\n"
    result += f"📊 **총 주차 공간**: {lot.total_spaces}개\n"
    result += f"🚗 **현재 주차된 차량**: {lot.current_cars}대\n"
    result += f"🆓 **사용 가능한 공간**: {lot.get_available_spaces()}개\n"
    result += f"💰 **유형**: {lot.parking_type}\n"
    result += f"💵 **가격**: {lot.price_info}\n\n"
    
    # 전기차 충전소 정보
    charger_info = get_ev_charger_info(lot_name)
    if charger_info and charger_info.get('has_charger'):
        chargers = charger_info.get('chargers', [])
        fast_count = sum(1 for c in chargers if c['charge_type'] == '급속')
        slow_count = sum(1 for c in chargers if c['charge_type'] == '완속')
        available_count = sum(1 for c in chargers if c['is_available'])
        
        result += f"🔌 **전기차 충전소**: ✅ 있음\n"
        result += f"   - 총 {len(chargers)}개 충전소 (급속 {fast_count}개, 완속 {slow_count}개)\n"
        result += f"   - 이용 가능: {available_count}개\n"
        
        # 충전소별 상세 정보
        if chargers:
            result += "\n   **충전소 상세 정보**:\n"
            for i, charger in enumerate(chargers, 1):
                result += f"   {i}. {charger['charger_name']}\n"
                result += f"      - 타입: {charger['charge_type']}\n"
                result += f"      - 이용 가능: {'✅ 가능' if charger['is_available'] else '❌ 불가능'}\n"
                result += f"      - 비용: {charger['cost']}\n"
                if charger.get('capacity'):
                    result += f"      - 용량: {charger['capacity']}\n"
                if charger.get('available_time'):
                    result += f"      - 이용 시간: {charger['available_time']}\n"
    else:
        result += f"🔌 **전기차 충전소**: ❌ 없음\n"
    
    result += "\n"
    
    # 점유율 정보
    occupancy_rate = lot.get_occupancy_rate()
    result += f"📈 **점유율**: {occupancy_rate:.1%}\n\n"
    
    # 상태 정보
    if lot.is_full():
        result += "🔴 **상태**: 가득 참\n"
    elif lot.is_empty():
        result += "🟢 **상태**: 비어있음\n"
    else:
        result += "🟡 **상태**: 부분 점유\n"
    
    # 시각적 표시
    visual_bar = '█' * int(occupancy_rate * 20) + '░' * (20 - int(occupancy_rate * 20))
    result += f"\n📊 **현황**: {visual_bar} {occupancy_rate:.1%}"
    
    return result

def update_lot_status(dong_name: str, lot_name: str) -> Tuple[str, str]:
    """주차장 상태를 업데이트하고 결과를 반환합니다."""
    global manager
    if not manager or not dong_name or not lot_name:
        return "❌ 동과 주차장을 선택해주세요.", ""
    
    dong = manager.get_dong(dong_name)
    if not dong:
        return f"❌ '{dong_name}' 동을 찾을 수 없습니다.", ""
    
    lot = dong.get_lot_by_name(lot_name)
    if not lot:
        return f"❌ '{lot_name}' 주차장을 찾을 수 없습니다.", ""
    
    # 주차장 상태 랜덤 업데이트
    update_result = lot.update_vehicle_count()
    
    # 변화 알림
    change = update_result['change']
    if update_result['action'] == "진입":
        change_msg = f"🚗 차량 {change}대 진입!"
    elif update_result['action'] == "출차":
        change_msg = f"🚙 차량 {abs(change)}대 출차!"
    else:
        change_msg = "⏸️ 변화 없음"
    
    # 업데이트된 상세 정보
    detail_info = get_lot_detail(dong_name, lot_name)
    
    return change_msg, detail_info

def run_simulation() -> str:
    """전체 현황을 확인합니다."""
    global manager
    if not manager:
        return "❌ 시스템이 초기화되지 않았습니다."
    
    try:
        # 모든 주차장 상태 업데이트
        manager.update_all_lots()
        
        # 전체 현황 수집
        result = "🎯 **전체 현황 확인 완료**\n"
        result += "=" * 50 + "\n\n"
        
        dong_names = manager.get_dong_names()
        for dong_name in dong_names:
            result += get_parking_status(dong_name) + "\n"
        
        return result
        
    except Exception as e:
        return f"❌ 현황 확인 중 오류 발생: {e}"

# ==================== 지도 연동 함수들 ====================
def get_coordinates_from_address(address: str) -> Tuple[float, float]:
    """주소를 좌표로 변환 (Nominatim API 사용)"""
    try:
        # OpenStreetMap Nominatim API
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        headers = {
            'User-Agent': 'ParkingManagementSystem/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                return lat, lon
    except Exception as e:
        print(f"좌표 변환 실패: {e}")
    
    # 기본 좌표 반환 (순천시청)
    return 34.9506, 127.4872

def open_naver_maps(dong_name: str, lot_name: str) -> Tuple[str, str]:
    """주차장 위치를 지도에 표시"""
    try:
        if not dong_name or not lot_name:
            return "❌ 동과 주차장을 선택해주세요.", ""
        
        # 주차장 정보 가져오기
        dong = manager.get_dong(dong_name)
        if not dong:
            return f"❌ '{dong_name}' 동을 찾을 수 없습니다.", ""
        
        lot = dong.get_lot_by_name(lot_name)
        if not lot:
            return f"❌ '{lot_name}' 주차장을 찾을 수 없습니다.", ""
        
        # 주소에서 좌표 추출
        lat, lon = get_coordinates_from_address(lot.location_info)
        
        # 네이버 지도 외부 링크
        search_query = lot.location_info
        naver_url = f"https://map.naver.com/v5/search/{urllib.parse.quote(search_query)}"
        
        # Leaflet.js를 사용한 OpenStreetMap 임베딩
        map_html = f"""
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        
        <div style="width: 100%; border: 2px solid #ddd; border-radius: 8px; overflow: hidden; background: #f5f5f5; padding: 15px;">
            <div id="map" style="height: 500px; border-radius: 8px; margin-bottom: 10px;"></div>
            <div style="text-align: center; padding: 10px;">
                <a href="{naver_url}" target="_blank" style="display: inline-block; margin: 5px; padding: 10px 20px; background: #03C75A; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
                    🗺️ 네이버 지도에서 열기
                </a>
            </div>
        </div>
        
        <script>
            // 지도 초기화
            var map = L.map('map').setView([{lat}, {lon}], 16);
            
            // OpenStreetMap 타일 레이어 추가
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            }}).addTo(map);
            
            // 마커 추가
            var marker = L.marker([{lat}, {lon}]).addTo(map);
            marker.bindPopup("<b>{lot.name}</b><br>{lot.location_info}").openPopup();
        </script>
        """
        
        status_msg = f"🗺️ **{lot_name} 위치**\n\n📍 주소: {lot.location_info}\n📌 좌표: {lat:.6f}, {lon:.6f}"
        
        return status_msg, map_html
    except Exception as e:
        return f"❌ 지도 열기 실패: {str(e)}", ""

# ==================== 사용자 인증 관련 함수들 ====================
def handle_login(username: str, password: str):
    """로그인 처리"""
    global auth_system
    if not auth_system:
        return "", "❌ 인증 시스템이 초기화되지 않았습니다.", gr.update(visible=False)
    
    success, message = auth_system.login(username, password)
    if success:
        fav_count = auth_system.get_favorites_count(username)
        return (
            username,
            f"✅ {message} (즐겨찾기: {fav_count}개)",
            gr.update(visible=True)
        )
    else:
        return "", f"❌ {message}", gr.update(visible=False)

def handle_register(username: str, password: str, password2: str, email: str):
    """회원가입 처리"""
    global auth_system
    if not auth_system:
        return "❌ 인증 시스템이 초기화되지 않았습니다."
    
    if password != password2:
        return "❌ 비밀번호가 일치하지 않습니다."
    
    success, message = auth_system.register(username, password, email)
    if success:
        return f"✅ {message}"
    else:
        return f"❌ {message}"

def handle_logout():
    """로그아웃 처리"""
    return "", "👤 로그인하지 않음", gr.update(visible=False)

def handle_add_favorite(username: str, dong_name: str, lot_name: str):
    """즐겨찾기 추가"""
    global auth_system
    if not username:
        return "❌ 로그인이 필요합니다.", gr.update(), gr.update()
    
    if not dong_name or not lot_name:
        return "❌ 지역과 주차장을 선택해주세요.", gr.update(), gr.update()
    
    success, message = auth_system.add_favorite(username, dong_name, lot_name)
    favorites_display = show_favorites(username)
    dong_choices = get_favorite_dongs(username)
    return (f"✅ {message}" if success else f"⚠️ {message}"), favorites_display, gr.update(choices=dong_choices)

def handle_remove_favorite(username: str, dong_name: str, lot_name: str):
    """즐겨찾기 삭제"""
    global auth_system
    if not username:
        return "❌ 로그인이 필요합니다.", gr.update(), gr.update()
    
    if not dong_name or not lot_name:
        return "❌ 지역과 주차장을 선택해주세요.", gr.update(), gr.update()
    
    success, message = auth_system.remove_favorite(username, dong_name, lot_name)
    favorites_display = show_favorites(username)
    dong_choices = get_favorite_dongs(username)
    return (f"✅ {message}" if success else f"❌ {message}"), favorites_display, gr.update(choices=dong_choices)

def handle_clear_favorites(username: str):
    """즐겨찾기 전체 삭제"""
    global auth_system
    if not username:
        return "❌ 로그인이 필요합니다.", gr.update(), gr.update()
    
    success, message = auth_system.clear_favorites(username)
    favorites_display = show_favorites(username)
    dong_choices = get_favorite_dongs(username)
    return (f"✅ {message}" if success else f"❌ {message}"), favorites_display, gr.update(choices=dong_choices)

def show_favorites(username: str) -> str:
    """즐겨찾기 목록 표시 (주차장 현황 탭 스타일)"""
    from parking_data import get_ev_charger_info
    global auth_system, manager
    if not username:
        return "**👤 로그인 후 이용하세요.**\n\n개인별 즐겨찾기 기능을 사용하려면 로그인이 필요합니다."
    
    favorites = auth_system.get_favorites(username)
    if not favorites:
        return "**📝 즐겨찾기가 비어있습니다.**\n\n왼쪽 하단에서 주차장을 추가해보세요!"
    
    # 동별로 그룹화
    dongs_dict = {}
    for fav in favorites:
        dong_name = fav['dong_name']
        if dong_name not in dongs_dict:
            dongs_dict[dong_name] = []
        dongs_dict[dong_name].append(fav)
    
    result = f"⭐ **즐겨찾기 주차장 현황** (총 {len(favorites)}개)\n"
    result += "=" * 50 + "\n\n"
    
    # 동별로 현황 표시 (주차장 현황 탭과 동일한 스타일)
    for dong_name, favs in dongs_dict.items():
        result += f"🏘️ **{dong_name} 주차장 현황**\n"
        result += "=" * 50 + "\n\n"
        
        dong = manager.get_dong(dong_name) if manager else None
        
        for fav in favs:
            lot_name = fav['lot_name']
            
            if dong:
                lot = dong.get_lot_by_name(lot_name)
                if lot:
                    occupancy_rate = lot.get_occupancy_rate()
                    available_spaces = lot.get_available_spaces()
                    
                    # 혼잡도 상태 아이콘 및 텍스트
                    if occupancy_rate >= 0.9:
                        status_icon = "🔴"
                        status_text = "매우 혼잡"
                    elif occupancy_rate >= 0.7:
                        status_icon = "🟠"
                        status_text = "혼잡"
                    elif occupancy_rate >= 0.4:
                        status_icon = "🟡"
                        status_text = "보통"
                    else:
                        status_icon = "🟢"
                        status_text = "여유"
                    
                    # 전기차 충전소 정보 먼저 확인
                    charger_info = get_ev_charger_info(lot_name)
                    has_charger = charger_info and charger_info.get('has_charger')
                    
                    # 유형에 따른 시각적 구분 (전기차 충전소 아이콘 추가)
                    charger_icon = "🔌" if has_charger else ""
                    if lot.parking_type == "유료":
                        result += f"🔴 **[유료] {charger_icon} {lot.name}** ⭐\n"
                    else:
                        result += f"🟢 **[무료] {charger_icon} {lot.name}** ⭐\n"
                    
                    result += f"📍 주소: {lot.location_info}\n"
                    result += f"🚗 현재: {lot.current_cars}/{lot.total_spaces} ({occupancy_rate:.1%})\n"
                    result += f"🆓 여유: {available_spaces}개\n"
                    result += f"💰 유형: {lot.parking_type}\n"
                    result += f"💵 가격: {lot.price_info}\n"
                    
                    # 전기차 충전소 정보 표시
                    if has_charger:
                        chargers = charger_info.get('chargers', [])
                        fast_count = sum(1 for c in chargers if c['charge_type'] == '급속')
                        slow_count = sum(1 for c in chargers if c['charge_type'] == '완속')
                        available_count = sum(1 for c in chargers if c['is_available'])
                        result += f"🔌 **전기차 충전소**: ✅ **있음** (급속 {fast_count}개, 완속 {slow_count}개, 이용가능 {available_count}개)\n"
                    else:
                        result += f"🔌 **전기차 충전소**: ❌ 없음\n"
                    result += f"{status_icon} **혼잡도**: {status_text}\n"
                    
                    # 시각적 표시
                    visual_bar = '█' * int(occupancy_rate * 15) + '░' * (15 - int(occupancy_rate * 15))
                    result += f"📊 {visual_bar} {occupancy_rate:.1%}\n\n"
                else:
                    result += f"🅿️ **{lot_name}** ⭐\n"
                    result += "   ⚠️ 주차장 정보를 찾을 수 없습니다.\n\n"
            else:
                result += f"🅿️ **{lot_name}** ⭐\n"
                result += "   ⚠️ 동 정보를 찾을 수 없습니다.\n\n"
        
        result += "\n"
    
    return result

def get_favorite_dongs(username: str) -> List[str]:
    """즐겨찾기에서 동 목록 추출"""
    global auth_system
    if not username or not auth_system:
        return []
    
    favorites = auth_system.get_favorites(username)
    # 중복 제거하고 동 목록 반환
    dongs = list(set([fav['dong_name'] for fav in favorites]))
    return sorted(dongs)

def get_favorite_lots_by_dong(username: str, dong_name: str) -> List[str]:
    """특정 동의 즐겨찾기 주차장 목록"""
    global auth_system
    if not username or not auth_system or not dong_name:
        return []
    
    favorites = auth_system.get_favorites(username)
    lots = [fav['lot_name'] for fav in favorites if fav['dong_name'] == dong_name]
    return lots

def update_favorite_dong_choices(username: str):
    """즐겨찾기 동 목록 업데이트"""
    if not username:
        return gr.update(choices=[])
    
    dongs = get_favorite_dongs(username)
    return gr.update(choices=dongs, value=None)

def update_favorite_single(username: str, dong_name: str, lot_name: str) -> str:
    """즐겨찾기 개별 주차장 새로고침 (주차장 현황 탭 스타일)"""
    global manager
    from parking_data import get_ev_charger_info
    
    if not username:
        return "❌ 로그인이 필요합니다."
    
    if not dong_name or not lot_name:
        return "❌ 지역과 주차장을 선택해주세요."
    
    if not manager:
        return "❌ 시스템이 초기화되지 않았습니다."
    
    dong = manager.get_dong(dong_name)
    if not dong:
        return f"❌ '{dong_name}' 동을 찾을 수 없습니다."
    
    lot = dong.get_lot_by_name(lot_name)
    if not lot:
        return f"❌ '{lot_name}' 주차장을 찾을 수 없습니다."
    
    # 주차장 상태 업데이트
    update_result = lot.update_vehicle_count()
    
    # 변화 알림
    change = update_result['change']
    if update_result['action'] == "진입":
        change_msg = f"🚗 차량 {change}대 진입!"
    elif update_result['action'] == "출차":
        change_msg = f"🚙 차량 {abs(change)}대 출차!"
    else:
        change_msg = "⏸️ 변화 없음"
    
    # 상세 정보 (주차장 현황 탭과 동일한 스타일)
    result = f"🔄 **{lot_name} 새로고침**\n"
    result += "=" * 50 + "\n\n"
    result += f"{change_msg}\n\n"
    result += f"🅿️ **{lot.name} 상세 정보**\n"
    result += "=" * 50 + "\n\n"
    
    # 기본 정보
    result += f"📍 **주소**: {lot.location_info}\n"
    result += f"📊 **총 주차 공간**: {lot.total_spaces}개\n"
    result += f"🚗 **현재 주차된 차량**: {lot.current_cars}대\n"
    result += f"🆓 **사용 가능한 공간**: {lot.get_available_spaces()}개\n"
    result += f"💰 **유형**: {lot.parking_type}\n"
    result += f"💵 **가격**: {lot.price_info}\n\n"
    
    # 전기차 충전소 정보
    charger_info = get_ev_charger_info(lot_name)
    if charger_info and charger_info.get('has_charger'):
        chargers = charger_info.get('chargers', [])
        fast_count = sum(1 for c in chargers if c['charge_type'] == '급속')
        slow_count = sum(1 for c in chargers if c['charge_type'] == '완속')
        available_count = sum(1 for c in chargers if c['is_available'])
        
        result += f"🔌 **전기차 충전소**: ✅ **있음**\n"
        result += f"   - 총 {len(chargers)}개 충전소 (급속 {fast_count}개, 완속 {slow_count}개)\n"
        result += f"   - 이용 가능: {available_count}개\n"
    else:
        result += f"🔌 **전기차 충전소**: ❌ 없음\n"
    
    result += "\n"
    
    # 점유율 정보
    occupancy_rate = lot.get_occupancy_rate()
    result += f"📈 **점유율**: {occupancy_rate:.1%}\n\n"
    
    # 상태 정보
    if lot.is_full():
        result += "🔴 **상태**: 가득 참\n"
    elif lot.is_empty():
        result += "🟢 **상태**: 비어있음\n"
    else:
        result += "🟡 **상태**: 부분 점유\n"
    
    # 시각적 표시
    visual_bar = '█' * int(occupancy_rate * 20) + '░' * (20 - int(occupancy_rate * 20))
    result += f"\n📊 **현황**: {visual_bar} {occupancy_rate:.1%}"
    
    return result

def simulate_all_favorites(username: str) -> str:
    """즐겨찾기 전체 현황 확인 (주차장 현황 탭 스타일)"""
    global auth_system, manager
    
    if not username:
        return "❌ 로그인이 필요합니다."
    
    if not manager:
        return "❌ 시스템이 초기화되지 않았습니다."
    
    favorites = auth_system.get_favorites(username)
    if not favorites:
        return "❌ 즐겨찾기가 비어있습니다."
    
    # 모든 주차장 상태 업데이트
    for fav in favorites:
        dong = manager.get_dong(fav['dong_name'])
        if dong:
            lot = dong.get_lot_by_name(fav['lot_name'])
            if lot:
                lot.update_vehicle_count()
    
    # 전체 현황 출력 (주차장 현황 탭 스타일)
    result = "🎯 **즐겨찾기 전체 현황 확인**\n"
    result += "=" * 50 + "\n\n"
    
    # 동별로 그룹화
    dongs_dict = {}
    for fav in favorites:
        dong_name = fav['dong_name']
        if dong_name not in dongs_dict:
            dongs_dict[dong_name] = []
        dongs_dict[dong_name].append(fav['lot_name'])
    
    # 동별로 현황 표시
    for dong_name, lot_names in dongs_dict.items():
        result += f"🏘️ **{dong_name} 주차장 현황**\n"
        result += "=" * 50 + "\n\n"
        
        dong = manager.get_dong(dong_name)
        if dong:
            for lot_name in lot_names:
                lot = dong.get_lot_by_name(lot_name)
                if lot:
                    occupancy_rate = lot.get_occupancy_rate()
                    available_spaces = lot.get_available_spaces()
                    
                    # 혼잡도 상태 아이콘 및 텍스트
                    if occupancy_rate >= 0.9:
                        status_icon = "🔴"
                        status_text = "매우 혼잡"
                    elif occupancy_rate >= 0.7:
                        status_icon = "🟠"
                        status_text = "혼잡"
                    elif occupancy_rate >= 0.4:
                        status_icon = "🟡"
                        status_text = "보통"
                    else:
                        status_icon = "🟢"
                        status_text = "여유"
                    
                    # 유형에 따른 시각적 구분
                    if lot.parking_type == "유료":
                        result += f"🔴 **[유료] {lot.name}**\n"
                    else:
                        result += f"🟢 **[무료] {lot.name}**\n"
                    
                    result += f"📍 주소: {lot.location_info}\n"
                    result += f"🚗 현재: {lot.current_cars}/{lot.total_spaces} ({occupancy_rate:.1%})\n"
                    result += f"🆓 여유: {available_spaces}개\n"
                    result += f"💰 유형: {lot.parking_type}\n"
                    result += f"💵 가격: {lot.price_info}\n"
                    result += f"{status_icon} **혼잡도**: {status_text}\n"
                    
                    # 시각적 표시
                    visual_bar = '█' * int(occupancy_rate * 15) + '░' * (15 - int(occupancy_rate * 15))
                    result += f"📊 {visual_bar} {occupancy_rate:.1%}\n\n"
        
        result += "\n"
    
    return result

def handle_change_password(username: str, current_pw: str, new_pw: str, new_pw2: str):
    """비밀번호 변경"""
    global auth_system
    if not username:
        return "❌ 로그인이 필요합니다."
    
    if new_pw != new_pw2:
        return "❌ 새 비밀번호가 일치하지 않습니다."
    
    success, message = auth_system.change_password(username, current_pw, new_pw)
    return f"✅ {message}" if success else f"❌ {message}"

def handle_delete_account(username: str, password: str):
    """계정 삭제"""
    global auth_system
    if not username:
        return "❌ 로그인이 필요합니다.", gr.update()
    
    success, message = auth_system.delete_account(username, password)
    if success:
        return f"✅ {message}", "", "👤 로그인하지 않음", gr.update(visible=False)
    else:
        return f"❌ {message}", username, gr.update(), gr.update()

def show_account_info(username: str) -> str:
    """계정 정보 표시"""
    global auth_system
    if not username:
        return "**로그인이 필요합니다.**"
    
    user_info = auth_system.get_user_info(username)
    if not user_info:
        return "**사용자 정보를 불러올 수 없습니다.**"
    
    result = f"# 👤 {username}님의 계정 정보\n\n"
    result += "=" * 50 + "\n\n"
    
    # 가입 정보
    try:
        created_at = datetime.fromisoformat(user_info['created_at']).strftime("%Y-%m-%d %H:%M")
    except:
        created_at = "알 수 없음"
    
    result += f"**📅 가입일:** {created_at}\n"
    result += f"**📧 이메일:** {user_info.get('email', '등록 안 됨')}\n"
    result += f"**⭐ 즐겨찾기:** {len(user_info.get('favorites', []))}개\n\n"
    
    # 마지막 로그인
    if user_info.get('last_login'):
        try:
            last_login = datetime.fromisoformat(user_info['last_login']).strftime("%Y-%m-%d %H:%M")
            result += f"**🕐 마지막 로그인:** {last_login}\n"
        except:
            pass
    
    return result

# ==================== 주차 요금 관리 함수들 ====================

def get_paid_parking_lots(dong_name: str) -> List[str]:
    """유료 주차장 목록 반환"""
    global manager
    if not manager or not dong_name:
        return []
    
    dong = manager.get_dong(dong_name)
    if not dong:
        return []
    
    paid_lots = []
    for lot in dong.parking_lots:
        if lot.parking_type == "유료":
            paid_lots.append(lot.name)
    
    return paid_lots

def handle_parking_entry(username: str, dong_name: str, lot_name: str) -> Tuple[str, str]:
    """입차 처리"""
    global auth_system, manager
    if not username:
        return "❌ 로그인이 필요합니다.", ""
    
    if not dong_name or not lot_name:
        return "❌ 동과 주차장을 선택해주세요.", ""
    
    # 주차장 정보 조회
    dong = manager.get_dong(dong_name)
    if not dong:
        return f"❌ '{dong_name}' 동을 찾을 수 없습니다.", ""
    
    lot = dong.get_lot_by_name(lot_name)
    if not lot:
        return f"❌ '{lot_name}' 주차장을 찾을 수 없습니다.", ""
    
    # 유료 주차장인지 확인
    if lot.parking_type != "유료":
        return "❌ 유료 주차장만 입차할 수 있습니다.", ""
    
    # 입차 처리
    success, message = auth_system.start_parking(username, dong_name, lot_name, lot.price_info)
    if success:
        return f"✅ {message}", show_current_parking_info(username)
    else:
        return f"❌ {message}", ""

def show_current_parking_info(username: str) -> str:
    """현재 주차 정보 표시"""
    global auth_system
    if not username:
        return "❌ 로그인이 필요합니다."
    
    parking_info = auth_system.get_current_parking(username)
    if not parking_info:
        return "**🚗 현재 주차 중이 아닙니다.**"
    
    # 주차 시간 정보
    duration_info = get_parking_duration_info(parking_info['entry_time'])
    if not duration_info['success']:
        return f"❌ 주차 시간 정보 조회 실패: {duration_info['error']}"
    
    # 현재 요금 계산
    current_fee = calculate_current_fee(parking_info['entry_time'], parking_info['price_info'])
    
    result = f"# 🅿️ 현재 주차 정보\n\n"
    result += "=" * 50 + "\n\n"
    result += f"**📍 주차장**: {parking_info['dong_name']} - {parking_info['lot_name']}\n"
    result += f"**⏰ 입차 시간**: {datetime.fromisoformat(parking_info['entry_time']).strftime('%Y-%m-%d %H:%M:%S')}\n"
    result += f"**⏱️ 경과 시간**: {duration_info['formatted_duration']}\n"
    result += f"**💰 가격 정보**: {parking_info['price_info']}\n\n"
    
    # 실시간 요금 정보
    if current_fee['success']:
        result += format_fee_result(current_fee)
    else:
        result += f"❌ 요금 계산 실패: {current_fee.get('error', '알 수 없는 오류')}"
    
    return result

def handle_parking_exit(username: str) -> Tuple[str, str]:
    """출차 처리"""
    global auth_system
    if not username:
        return "❌ 로그인이 필요합니다.", ""
    
    # 현재 주차 정보 조회
    parking_info = auth_system.get_current_parking(username)
    if not parking_info:
        return "❌ 주차 기록이 없습니다.", ""
    
    # 최종 요금 계산
    current_time = datetime.now().isoformat()
    final_fee = calculate_fee_with_thinking(parking_info['entry_time'], current_time, parking_info['price_info'])
    
    # 출차 처리
    success, message = auth_system.end_parking(username)
    if success:
        result = f"✅ {message}\n\n"
        result += "=" * 50 + "\n"
        result += "**📋 최종 주차 요금**\n"
        result += "=" * 50 + "\n\n"
        result += format_fee_result(final_fee)
        return result, "**🚗 현재 주차 중이 아닙니다.**"
    else:
        return f"❌ {message}", show_current_parking_info(username)

def refresh_parking_fee(username: str) -> str:
    """요금 새로고침"""
    if not username:
        return "❌ 로그인이 필요합니다."
    
    return show_current_parking_info(username)

def calculate_estimated_parking_fee(username: str, estimated_exit_time: str) -> str:
    """예상 출차시간 기준 요금 계산"""
    global auth_system
    if not username:
        return "❌ 로그인이 필요합니다."
    
    parking_info = auth_system.get_current_parking(username)
    if not parking_info:
        return "❌ 현재 주차 중이 아닙니다."
    
    # 예상 출차시간 유효성 검사
    try:
        from datetime import datetime
        estimated_dt = datetime.fromisoformat(estimated_exit_time)
        entry_dt = datetime.fromisoformat(parking_info['entry_time'])
        
        if estimated_dt <= entry_dt:
            return "❌ 예상 출차시간은 입차시간보다 늦어야 합니다."
    except:
        return "❌ 올바른 시간 형식을 입력해주세요. (예: 2024-01-01T12:30:00)"
    
    # 예상 요금 계산
    result = calculate_estimated_fee(parking_info['entry_time'], estimated_exit_time, parking_info['price_info'])
    if result['success']:
        return format_estimated_fee_result(result, estimated_exit_time)
    else:
        return f"❌ 예상 요금 계산 실패: {result.get('error', '알 수 없는 오류')}"

# ==================== Gradio 인터페이스 생성 ====================
def create_gradio_interface():
    """Gradio 인터페이스를 생성합니다."""
    
    with gr.Blocks(
        title="🚗 주차장 관리 시스템",
        theme=gr.themes.Soft(),
        css="""
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .status-box {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        """
    ) as interface:
        
        # 로그인 상태 저장 (세션)
        current_user = gr.State("")
        
        gr.Markdown(
            """
            # 🚗 주차장 관리 시스템
            
            동별 주차장 현황을 확인하고 실시간 시뮬레이션을 실행할 수 있습니다.
            """,
            elem_classes="main-container"
        )
        
        # ==================== 로그인 바 ====================
        with gr.Row():
            with gr.Column(scale=3):
                user_status_display = gr.Markdown("**👤 로그인하지 않음**")
            
            with gr.Column(scale=1):
                logout_btn = gr.Button("🚪 로그아웃", size="sm", visible=False)
        
        with gr.Accordion("🔐 로그인 / 회원가입", open=False):
            with gr.Tabs():
                # 로그인 탭
                with gr.Tab("로그인"):
                    login_username = gr.Textbox(label="아이디", placeholder="아이디를 입력하세요")
                    login_password = gr.Textbox(label="비밀번호", type="password", placeholder="비밀번호를 입력하세요")
                    login_btn = gr.Button("로그인", variant="primary")
                    login_msg = gr.Markdown()
                
                # 회원가입 탭
                with gr.Tab("회원가입"):
                    reg_username = gr.Textbox(label="아이디", placeholder="3자 이상")
                    reg_password = gr.Textbox(label="비밀번호", type="password", placeholder="4자 이상")
                    reg_password2 = gr.Textbox(label="비밀번호 확인", type="password")
                    reg_email = gr.Textbox(label="이메일 (선택)", placeholder="example@email.com")
                    reg_btn = gr.Button("회원가입", variant="primary")
                    reg_msg = gr.Markdown()
        
        gr.Markdown("---")
        
        # ==================== 메인 탭 ====================
        with gr.Tabs():
            # 주차장 현황 탭
            with gr.Tab("🏘️ 주차장 현황"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 🏘️ 지역선택")
                        dong_dropdown = gr.Dropdown(
                            choices=get_dong_list(),
                            label="지역을 선택하세요",
                            value=None,
                            interactive=True
                        )
                        
                        gr.Markdown("### 🅿️ 주차장 선택")
                        lot_dropdown = gr.Dropdown(
                            choices=[],
                            label="주차장을 선택하세요",
                            interactive=True
                        )
                        
                        with gr.Row():
                            status_btn = gr.Button("📊 현황 확인", variant="primary")
                            update_btn = gr.Button("🔄 새로고침", variant="secondary")
                        
                        with gr.Row():
                            naver_maps_btn = gr.Button("🗺️ 네이버 지도", variant="primary")
                        
                        with gr.Row():
                            simulation_btn = gr.Button("🎯 전체 현황 확인", variant="stop")
                    
                    with gr.Column(scale=2):
                        gr.Markdown("### 📋 주차장 현황")
                        status_output = gr.Markdown(
                            "동을 선택하고 현황을 확인해보세요.",
                            elem_classes="status-box"
                        )
                        
                        gr.Markdown("### 🗺️ 지도")
                        map_output = gr.HTML(
                            "<div style='text-align:center; padding:50px; color:#999;'>주차장을 선택하고 '🗺️ 네이버 지도' 버튼을 클릭하세요.</div>"
                        )
            
            # 내 즐겨찾기 탭
            with gr.Tab("⭐ 내 즐겨찾기"):
                with gr.Row():
                    # 좌측: 즐겨찾기 제어
                    with gr.Column(scale=1):
                        gr.Markdown("### 🎯 즐겨찾기 제어")
                        
                        # 개별 업데이트용 선택
                        fav_select_dong = gr.Dropdown(
                            choices=[],
                            label="지역선택",
                            value=None,
                            interactive=True
                        )
                        fav_select_lot = gr.Dropdown(
                            choices=[],
                            label="주차장 선택",
                            value=None,
                            interactive=True
                        )
                        
                        with gr.Row():
                            fav_update_single_btn = gr.Button("🔄 새로고침", variant="primary")
                        
                        with gr.Row():
                            fav_simulate_all_btn = gr.Button("🎯 전체 현황 확인", variant="secondary")
                        
                        gr.Markdown("---")
                        gr.Markdown("### ➕ 즐겨찾기 관리")
                        
                        fav_dong = gr.Dropdown(
                            choices=get_dong_list(),
                            label="지역선택",
                            value=None
                        )
                        fav_lot = gr.Dropdown(
                            choices=[],
                            label="주차장 선택",
                            value=None
                        )
                        
                        with gr.Row():
                            add_fav_btn = gr.Button("⭐ 추가", variant="primary")
                            remove_fav_btn = gr.Button("🗑️ 삭제", variant="secondary")
                        
                        with gr.Row():
                            clear_all_fav_btn = gr.Button("🗑️ 전체 삭제", variant="stop")
                        
                        fav_msg = gr.Markdown()
                    
                    # 우측: 현황 표시
                    with gr.Column(scale=2):
                        gr.Markdown("### 📋 즐겨찾기 현황")
                        favorites_display = gr.Markdown(
                            "로그인 후 이용하세요.",
                            elem_classes="status-box"
                        )
            
            # 계정 관리 탭
            with gr.Tab("⚙️ 계정 관리"):
                with gr.Row():
                    # 좌측: 계정 정보
                    with gr.Column(scale=1):
                        gr.Markdown("### 👤 계정 정보")
                        account_info_display = gr.Markdown("로그인이 필요합니다.")
                        refresh_account_btn = gr.Button("🔄 새로고침", size="sm")
                    
                    # 우측: 계정 설정
                    with gr.Column(scale=1):
                        gr.Markdown("### 🔧 계정 설정")
                        
                        # 비밀번호 변경
                        with gr.Accordion("🔑 비밀번호 변경", open=False):
                            current_pw = gr.Textbox(label="현재 비밀번호", type="password")
                            new_pw = gr.Textbox(label="새 비밀번호", type="password")
                            new_pw2 = gr.Textbox(label="새 비밀번호 확인", type="password")
                            change_pw_btn = gr.Button("비밀번호 변경", variant="primary")
                            change_pw_msg = gr.Markdown()
                        
                        # 계정 삭제
                        with gr.Accordion("🗑️ 계정 삭제", open=False):
                            gr.Markdown("**⚠️ 경고: 이 작업은 되돌릴 수 없습니다!**")
                            delete_pw = gr.Textbox(label="비밀번호 확인", type="password")
                            delete_account_btn = gr.Button("계정 삭제", variant="stop")
                            delete_account_msg = gr.Markdown()
            
            # 주차 요금 관리 탭
            with gr.Tab("💰 주차 요금 관리"):
                gr.Markdown("### 🅿️ 주차 요금 계산 및 관리")
                gr.Markdown("**로그인 후 유료 주차장에 입차하여 요금을 계산할 수 있습니다.**")
                
                with gr.Row():
                    # 좌측: 입차 섹션
                    with gr.Column(scale=1):
                        gr.Markdown("#### 🚗 입차")
                        parking_dong_select = gr.Dropdown(
                            label="동 선택",
                            choices=[],
                            interactive=True
                        )
                        parking_lot_select = gr.Dropdown(
                            label="주차장 선택 (유료만 표시)",
                            choices=[],
                            interactive=True
                        )
                        parking_entry_btn = gr.Button("🚗 입차", variant="primary")
                        parking_entry_msg = gr.Markdown()
                    
                    # 우측: 현재 주차 정보
                    with gr.Column(scale=1):
                        gr.Markdown("#### 📊 현재 주차 정보")
                        current_parking_display = gr.Markdown("**🚗 현재 주차 중이 아닙니다.**")
                        refresh_fee_btn = gr.Button("🔄 요금 새로고침", size="sm")
                        
                        # 예상 출차시간 입력 섹션
                        gr.Markdown("#### 🔮 예상 출차시간 요금 계산")
                        estimated_exit_time = gr.Textbox(
                            label="예상 출차시간",
                            placeholder="2024-01-01T12:30:00",
                            info="ISO 형식으로 입력 (예: 2024-01-01T12:30:00)"
                        )
                        calculate_estimated_btn = gr.Button("💰 예상 요금 계산", variant="secondary")
                        estimated_fee_display = gr.Markdown()
                        
                        parking_exit_btn = gr.Button("🚪 출차", variant="stop")
                        parking_exit_msg = gr.Markdown()
            
            # 전기차 충전소 탭
            with gr.Tab("🔌 전기차 충전소"):
                gr.Markdown("### 🔌 전기차 충전소 정보")
                gr.Markdown("**충전소가 있는 주차장의 전기차 충전소 정보를 확인할 수 있습니다.**")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 🏘️ 지역선택")
                        ev_dong_dropdown = gr.Dropdown(
                            choices=[],
                            label="지역을 선택하세요",
                            value=None,
                            interactive=True
                        )
                        
                        gr.Markdown("### 🔌 충전소가 있는 주차장")
                        ev_lot_dropdown = gr.Dropdown(
                            choices=[],
                            label="주차장을 선택하세요",
                            interactive=True
                        )
                        
                        ev_refresh_btn = gr.Button("🔄 새로고침", variant="primary")
                    
                    with gr.Column(scale=2):
                        gr.Markdown("### 📋 전기차 충전소 정보")
                        ev_info_output = gr.Markdown(
                            "지역을 선택하고 주차장을 선택하세요.",
                            elem_classes="status-box"
                        )
            
        # ==================== 이벤트 핸들러 ====================
        
        # 로그인/로그아웃
        login_btn.click(
            fn=handle_login,
            inputs=[login_username, login_password],
            outputs=[current_user, login_msg, logout_btn]
        )
        
        reg_btn.click(
            fn=handle_register,
            inputs=[reg_username, reg_password, reg_password2, reg_email],
            outputs=[reg_msg]
        )
        
        logout_btn.click(
            fn=handle_logout,
            inputs=[],
            outputs=[current_user, user_status_display, logout_btn]
        )
        
        # 주차장 현황 탭 이벤트
        def on_dong_change(dong_name):
            """지역 선택이 변경될 때 주차장 목록을 업데이트"""
            lots = get_parking_lots(dong_name)
            return gr.Dropdown(choices=lots, value=None)
        
        def on_status_check(dong_name):
            """현황 확인 버튼 클릭 시"""
            if not dong_name:
                return "❌ 지역을 선택해주세요."
            
            # 주차장 상태 업데이트 (시뮬레이션)
            dong = manager.get_dong(dong_name)
            if dong:
                for lot in dong.parking_lots:
                    # 주차장 상태를 랜덤하게 업데이트
                    lot.simulate_parking_changes()
            
            return get_parking_status(dong_name)
        
        def on_lot_update(dong_name, lot_name):
            """주차장 새로고침"""
            if not dong_name or not lot_name:
                return "❌ 지역과 주차장을 선택해주세요."
            
            # 주차장 상태 업데이트
            change_msg, detail_info = update_lot_status(dong_name, lot_name)
            
            # 상태 변화와 상세 정보를 통합하여 반환
            result = f"🔄 **{lot_name} 새로고침**\n"
            result += "=" * 50 + "\n\n"
            result += f"{change_msg}\n\n"
            result += detail_info
            
            return result
        
        def on_simulation():
            """전체 현황 확인"""
            return run_simulation()
        
        dong_dropdown.change(
            fn=on_dong_change,
            inputs=[dong_dropdown],
            outputs=[lot_dropdown]
        )
        
        status_btn.click(
            fn=on_status_check,
            inputs=[dong_dropdown],
            outputs=[status_output]
        )
        
        update_btn.click(
            fn=on_lot_update,
            inputs=[dong_dropdown, lot_dropdown],
            outputs=[status_output]
        )
        
        simulation_btn.click(
            fn=on_simulation,
            inputs=[],
            outputs=[status_output]
        )
        
        naver_maps_btn.click(
            fn=open_naver_maps,
            inputs=[dong_dropdown, lot_dropdown],
            outputs=[status_output, map_output]
        )
        
        # 즐겨찾기 탭 이벤트
        
        # 즐겨찾기 지역 선택 시 주차장 목록 업데이트
        def on_fav_select_dong_change(username, dong_name):
            """즐겨찾기에서 지역 선택 시 주차장 목록 업데이트"""
            lots = get_favorite_lots_by_dong(username, dong_name)
            return gr.Dropdown(choices=lots, value=None)
        
        # 즐겨찾기 추가용 지역 선택 시
        def on_fav_dong_change(dong_name):
            """즐겨찾기 추가용 지역 선택 시"""
            lots = get_parking_lots(dong_name)
            return gr.Dropdown(choices=lots, value=None)
        
        # 즐겨찾기 선택 지역 변경 시
        fav_select_dong.change(
            fn=on_fav_select_dong_change,
            inputs=[current_user, fav_select_dong],
            outputs=[fav_select_lot]
        )
        
        # 개별 주차장 새로고침
        fav_update_single_btn.click(
            fn=update_favorite_single,
            inputs=[current_user, fav_select_dong, fav_select_lot],
            outputs=[favorites_display]
        )
        
        # 전체 현황 확인
        fav_simulate_all_btn.click(
            fn=simulate_all_favorites,
            inputs=[current_user],
            outputs=[favorites_display]
        )
        
        # 즐겨찾기 추가용 지역 선택
        fav_dong.change(
            fn=on_fav_dong_change,
            inputs=[fav_dong],
            outputs=[fav_lot]
        )
        
        add_fav_btn.click(
            fn=handle_add_favorite,
            inputs=[current_user, fav_dong, fav_lot],
            outputs=[fav_msg, favorites_display, fav_select_dong]
        )
        
        remove_fav_btn.click(
            fn=handle_remove_favorite,
            inputs=[current_user, fav_dong, fav_lot],
            outputs=[fav_msg, favorites_display, fav_select_dong]
        )
        
        clear_all_fav_btn.click(
            fn=handle_clear_favorites,
            inputs=[current_user],
            outputs=[fav_msg, favorites_display, fav_select_dong]
        )
        
        # 계정 관리 탭 이벤트
        refresh_account_btn.click(
            fn=show_account_info,
            inputs=[current_user],
            outputs=[account_info_display]
        )
        
        change_pw_btn.click(
            fn=handle_change_password,
            inputs=[current_user, current_pw, new_pw, new_pw2],
            outputs=[change_pw_msg]
        )
        
        delete_account_btn.click(
            fn=handle_delete_account,
            inputs=[current_user, delete_pw],
            outputs=[delete_account_msg, current_user, user_status_display, logout_btn]
        )
        
        # 로그인 상태 변경 시 사용자 상태 표시 및 즐겨찾기 동 목록 업데이트
        def on_user_change(username):
            """사용자 변경 시 UI 업데이트"""
            status = f"**👤 {username}**" if username else "**👤 로그인하지 않음**"
            dongs = get_favorite_dongs(username) if username else []
            return status, gr.Dropdown(choices=dongs, value=None)
        
        # 주차 요금 관리 탭 이벤트 핸들러
        
        # 동 선택 시 유료 주차장 목록 업데이트
        def on_parking_dong_change(dong_name):
            """주차 요금 관리에서 동 선택 시 유료 주차장 목록 업데이트"""
            if not dong_name:
                return gr.update(choices=[])
            
            paid_lots = get_paid_parking_lots(dong_name)
            return gr.update(choices=paid_lots)
        
        # 입차 처리
        def on_parking_entry(username, dong_name, lot_name):
            """입차 처리"""
            return handle_parking_entry(username, dong_name, lot_name)
        
        # 출차 처리
        def on_parking_exit(username):
            """출차 처리"""
            return handle_parking_exit(username)
        
        # 요금 새로고침
        def on_refresh_fee(username):
            """요금 새로고침"""
            return refresh_parking_fee(username)
        
        # 사용자 변경 시 주차 정보 업데이트
        def on_user_change_with_parking(username):
            """사용자 변경 시 주차 정보도 함께 업데이트"""
            status = f"**👤 {username}**" if username else "**👤 로그인하지 않음**"
            fav_choices = get_favorite_dongs(username) if username else []
            parking_info = show_current_parking_info(username) if username else "**🚗 현재 주차 중이 아닙니다.**"
            return status, gr.update(choices=fav_choices), parking_info, gr.update(choices=fav_choices)
        
        # 이벤트 연결
        parking_dong_select.change(
            fn=on_parking_dong_change,
            inputs=[parking_dong_select],
            outputs=[parking_lot_select]
        )
        
        parking_entry_btn.click(
            fn=on_parking_entry,
            inputs=[current_user, parking_dong_select, parking_lot_select],
            outputs=[parking_entry_msg, current_parking_display]
        )
        
        parking_exit_btn.click(
            fn=on_parking_exit,
            inputs=[current_user],
            outputs=[parking_exit_msg, current_parking_display]
        )
        
        refresh_fee_btn.click(
            fn=on_refresh_fee,
            inputs=[current_user],
            outputs=[current_parking_display]
        )
        
        # 예상 요금 계산
        def on_calculate_estimated_fee(username, estimated_exit_time):
            """예상 출차시간 기준 요금 계산"""
            return calculate_estimated_parking_fee(username, estimated_exit_time)
        
        calculate_estimated_btn.click(
            fn=on_calculate_estimated_fee,
            inputs=[current_user, estimated_exit_time],
            outputs=[estimated_fee_display]
        )
        
        # 주차 요금 관리 탭의 동 목록 초기화
        def initialize_parking_dong_choices():
            """주차 요금 관리 탭의 동 목록 초기화"""
            dong_names = [dong.name for dong in manager.dongs.values()]
            return gr.update(choices=dong_names)
        
        # 인터페이스 로드 시 동 목록 초기화
        interface.load(
            fn=initialize_parking_dong_choices,
            inputs=[],
            outputs=[parking_dong_select]
        )
        
        # 전기차 충전소 탭 이벤트
        from parking_data import get_ev_charger_lots_by_dong, get_ev_charger_info, load_ev_charger_data, get_dongs_with_chargers
        
        # 앱 시작 시 전기차 충전소 데이터 로드 및 지역 목록 초기화
        def initialize_ev_charger_data():
            """전기차 충전소 데이터를 초기화하고 충전소가 있는 지역만 표시합니다."""
            try:
                load_ev_charger_data()
                dongs_with_chargers = get_dongs_with_chargers()
                return gr.update(choices=dongs_with_chargers, value=None)
            except Exception as e:
                print(f"전기차 충전소 데이터 로드 실패: {e}")
                return gr.update(choices=[], value=None)
        
        # 인터페이스 로드 시 전기차 충전소 데이터 로드 및 지역 목록 업데이트
        interface.load(
            fn=initialize_ev_charger_data,
            inputs=[],
            outputs=[ev_dong_dropdown]
        )
        
        def get_ev_charger_lots_list(dong_name: str):
            """지역별 전기차 충전소가 있는 주차장 목록을 반환합니다."""
            if not dong_name:
                return gr.update(choices=[], value=None)
            try:
                lots = get_ev_charger_lots_by_dong(dong_name)
                return gr.update(choices=lots, value=None)
            except Exception as e:
                print(f"충전소가 있는 주차장 목록 조회 실패: {e}")
                return gr.update(choices=[], value=None)
        
        def display_ev_charger_info(lot_name: str) -> str:
            """전기차 충전소 정보를 표시합니다."""
            if not lot_name:
                return "주차장을 선택하세요."
            
            charger_info = get_ev_charger_info(lot_name)
            if not charger_info or not charger_info.get('has_charger'):
                return f"❌ **{lot_name}**에는 전기차 충전소가 없습니다."
            
            output = f"## 🔌 **{lot_name}** 전기차 충전소 정보\n\n"
            output += f"**충전소 유무**: ✅ **있음**\n\n"
            
            chargers = charger_info.get('chargers', [])
            if not chargers:
                return output + "충전소 정보가 없습니다."
            
            # 충전소별 정보 표시
            for i, charger in enumerate(chargers, 1):
                output += f"### 충전소 {i}\n"
                output += f"- **충전소명**: {charger['charger_name']}\n"
                output += f"- **충전 타입**: {charger['charge_type']}\n"
                output += f"- **충전 가능 여부**: {'✅ 가능' if charger['is_available'] else '❌ 불가능'}\n"
                output += f"- **비용**: {charger['cost']}\n"
                if charger.get('capacity'):
                    output += f"- **충전 용량**: {charger['capacity']}\n"
                if charger.get('available_time'):
                    output += f"- **이용 가능 시간**: {charger['available_time']}\n"
                output += "\n"
            
            # 요약 정보
            fast_count = sum(1 for c in chargers if c['charge_type'] == '급속')
            slow_count = sum(1 for c in chargers if c['charge_type'] == '완속')
            available_count = sum(1 for c in chargers if c['is_available'])
            
            output += "---\n"
            output += f"**📊 요약**: 총 {len(chargers)}개 충전소 (급속 {fast_count}개, 완속 {slow_count}개, 이용가능 {available_count}개)\n"
            
            return output
        
        ev_dong_dropdown.change(
            fn=get_ev_charger_lots_list,
            inputs=[ev_dong_dropdown],
            outputs=[ev_lot_dropdown]
        )
        
        ev_lot_dropdown.change(
            fn=display_ev_charger_info,
            inputs=[ev_lot_dropdown],
            outputs=[ev_info_output]
        )
        
        ev_refresh_btn.click(
            fn=get_ev_charger_lots_list,
            inputs=[ev_dong_dropdown],
            outputs=[ev_lot_dropdown]
        )

        current_user.change(
            fn=on_user_change_with_parking,
            inputs=[current_user],
            outputs=[user_status_display, fav_select_dong, current_parking_display, fav_select_dong]
        )
    
    return interface

# ==================== 메인 실행 함수 ====================
def main():
    """메인 실행 함수입니다."""
    global manager, auth_system
    
    # 로깅 설정
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 시스템 초기화
        manager = initialize_system()
        
        # 사용자 인증 시스템 초기화
        auth_system = UserAuthSystem()
        logger.info("사용자 인증 시스템 초기화 완료")
        
        # 데이터 설정
        if not setup_parking_data(manager):
            logger.error("데이터 설정 실패")
            return
        
        # Gradio 인터페이스 생성 및 실행
        interface = create_gradio_interface()
        
        logger.info("Gradio 인터페이스 시작")
        # 환경 변수에서 포트 설정 (기본값: 7860)
        import os
        port = int(os.environ.get("GRADIO_SERVER_PORT", 7860))
        
        # IP 주소 표시
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        print(f"🌐 로컬 네트워크 접속 URL: http://{local_ip}:{port}")
        print(f"🏠 로컬 접속 URL: http://localhost:{port}")
        
        interface.launch(
            server_name="0.0.0.0",
            server_port=port,
            share=True,
            show_error=True
        )
        
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류 발생: {e}")
        print(f"❌ 오류가 발생했습니다: {e}")

# ==================== 실행 코드 ====================
if __name__ == "__main__":
    main()
