# extract_ev_charger_data.py
"""전기차 충전소 CSV 파일에서 데이터를 읽어서 DONGS_DATA의 주차장과 매칭"""

import pandas as pd
import re
from typing import List, Dict, Tuple

def normalize_address(address: str) -> str:
    """주소 정규화"""
    if not address:
        return ""
    
    # "전라남도 순천시 조례1길 24" -> "전남 순천시 조례1길 24"
    if address.startswith("전라남도"):
        return address.replace("전라남도", "전남")
    elif address.startswith("전남"):
        return address
    
    return address

def extract_dong_from_address(address: str) -> str:
    """주소에서 동 이름을 추출"""
    if not address:
        return None
    
    # "전남 순천시 조례동 1807" -> "조례동"
    match = re.search(r'(\w+동)', address)
    if match:
        return match.group(1)
    
    return None

def extract_address_number(address: str) -> str:
    """주소에서 지번 추출 (예: "조례동 1807" -> "조례동 1807")"""
    if not address:
        return None
    
    match = re.search(r'(\w+동)\s*(\d+[-\d]*)', address)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    
    return None

def read_ev_charger_csv(csv_path: str) -> List[Dict]:
    """
    전기차 충전소 CSV 파일을 읽습니다.
    
    Args:
        csv_path: CSV 파일 경로
        
    Returns:
        list: 충전소 정보 리스트
    """
    try:
        df = pd.read_csv(csv_path, encoding='cp949')
        
        chargers = []
        for _, row in df.iterrows():
            charger = {
                'charger_name': row['충전소'],
                'address': normalize_address(row['주소']),
                'charger_type': row['충전기타입'],
                'capacity': row['충전용량'],
                'available_time': row['이용가능시간'],
                'facility_type': row['시설구분(대)'],
                'convenience': row.get(' 편의제공', '')
            }
            chargers.append(charger)
        
        print(f"✅ CSV 파일 읽기 성공 (인코딩: cp949, {len(chargers)}개 충전소)")
        return chargers
    
    except Exception as e:
        print(f"❌ CSV 파일 읽기 실패: {e}")
        return []

def match_charger_to_parking_lot(chargers: List[Dict], parking_lots: List[Tuple]) -> Dict[str, Dict]:
    """
    충전소를 주차장과 매칭합니다.
    
    중요: 이 함수는 parking_lots(DONGS_DATA)에 있는 주차장만 매칭합니다.
    DONGS_DATA에 없는 주차장은 절대 매칭되지 않습니다.
    
    Args:
        chargers: 충전소 정보 리스트
        parking_lots: DONGS_DATA의 주차장 리스트 (이 리스트에 있는 주차장만 매칭됨)
    
    Returns:
        Dict: {주차장명: 충전소 정보} - DONGS_DATA에 있는 주차장만 포함됨
    """
    matched = {}
    
    # 주차장 정보를 딕셔너리로 변환
    # parking_lots(DONGS_DATA)에 있는 주차장만 parking_dict에 저장됨
    parking_dict = {}
    for dong_name, lots in parking_lots:
        for lot_name, total_spaces, address, parking_type, price_info, charger_info in lots:
            normalized_address = normalize_address(address)
            parking_dict[lot_name] = {
                'dong_name': dong_name,
                'address': normalized_address,
                'address_number': extract_address_number(normalized_address)
            }
    
    # 충전소를 주차장과 매칭 (주소 기반)
    # DONGS_DATA의 주차장 주소를 기준으로 충전소 주소와 비교
    import re
    
    for charger in chargers:
        charger_address = normalize_address(charger['address'])
        charger_dong = extract_dong_from_address(charger_address)
        charger_address_number = extract_address_number(charger_address)
        
        best_match = None
        best_score = 0
        
        # parking_dict에 있는 주차장과만 비교 (DONGS_DATA에 있는 주차장만)
        for lot_name, lot_info in parking_dict.items():
            lot_dong = lot_info['dong_name']
            lot_address = lot_info['address']
            lot_address_number = lot_info['address_number']
            
            score = 0
            
            # 충전소명에 주차장 이름이 포함되어 있는지 확인
            charger_name = charger['charger_name']
            lot_name_in_charger = lot_name in charger_name or charger_name in lot_name
            
            # 주차장 이름의 주요 키워드 추출 (공통 단어 제외)
            common_words = {'주차장', '공영주차장', '공영', '주차', '제', '동', '지구', '타워', '수영장'}
            lot_name_keywords = [kw for kw in lot_name.split() if kw not in common_words and len(kw) >= 2]
            keyword_match = len(lot_name_keywords) > 0 and any(kw in charger_name for kw in lot_name_keywords)
            
            # 특수 케이스: "문화건강센터 수영장"과 "순천시문화건강센터" 매칭
            if '문화건강' in lot_name and '문화건강' in charger_name:
                keyword_match = True
                # 동 이름이 다르더라도 키워드 매칭이면 허용
                if charger_dong != lot_dong:
                    # 주소에 "수영장"이 포함되어 있으면 매칭
                    if '수영장' in charger_address or '수영장' in lot_address:
                        score += 70  # 키워드 매칭 + 수영장 키워드
                        if score > best_score and score >= 60:
                            best_score = score
                            best_match = lot_name
                        continue
            
            # 동 이름이 일치하지 않으면 스킵 (특수 케이스 제외)
            if charger_dong != lot_dong:
                continue
            
            # 1. 주소가 정확히 일치하는 경우 (가장 정확)
            if lot_address == charger_address:
                score += 100
            # 2. 주소의 지번이 정확히 일치하고 충전소명에 주차장 이름이 포함된 경우
            elif charger_address_number and lot_address_number:
                if charger_address_number == lot_address_number:
                    if lot_name_in_charger or keyword_match:
                        score += 80  # 지번 일치 + 이름 일치
            
            # 3. 주소의 일부가 일치하고 충전소명에 주차장 이름이 포함된 경우
            if lot_address_number and lot_address_number in charger_address:
                if lot_name_in_charger or keyword_match:
                    score += 60  # 주소 일부 일치 + 이름 일치
            
            # 최소 점수 60 이상 (주소가 정확히 일치하거나 지번+이름이 일치하는 경우만)
            if score > best_score and score >= 60:
                best_score = score
                best_match = lot_name
        
        if best_match:
            if best_match not in matched:
                matched[best_match] = {
                    'has_charger': True,
                    'chargers': []
                }
            
            # 충전 타입 파싱
            charger_type = charger['charger_type']
            capacity = charger.get('capacity', '')
            
            if 'DC' in charger_type or '급속' in capacity or '급속' in str(capacity):
                charge_type = "급속"
            elif 'AC' in charger_type or '완속' in capacity or '완속' in str(capacity):
                charge_type = "완속"
            else:
                charge_type = "급속"  # 기본값
            
            # 충전 가능 여부 (이용가능시간이 있으면 가능)
            is_available = True  # 기본값, 실제 데이터에 따라 수정 가능
            available_time = charger.get('available_time', '')
            if available_time and '이용불가' in str(available_time):
                is_available = False
            
            # 비용 정보 (CSV에 없으면 "무료" 또는 "별도 문의"로 표시)
            cost = "무료"  # 기본값, 실제 데이터에 따라 수정 필요
            
            matched[best_match]['chargers'].append({
                'charger_name': charger['charger_name'],
                'charge_type': charge_type,
                'is_available': is_available,
                'cost': cost,
                'capacity': capacity,
                'available_time': available_time,
                'facility_type': charger.get('facility_type', ''),
                'convenience': charger.get('convenience', '')
            })
    
    return matched

if __name__ == "__main__":
    # 테스트 코드
    from parking_data import DONGS_DATA
    
    csv_path = r"c:\Users\user\Downloads\전라남도 순천시_전기차 충전소 현황_20241127.csv"
    chargers = read_ev_charger_csv(csv_path)
    matched = match_charger_to_parking_lot(chargers, DONGS_DATA)
    
    print(f"\n=== 주차장과 매칭 ===\n")
    print(f"매칭된 주차장: {len(matched)}개\n")
    
    for lot_name, charger_info in matched.items():
        print(f"📍 {lot_name}")
        print(f"   충전소 수: {len(charger_info['chargers'])}개")
        for charger in charger_info['chargers']:
            print(f"   - {charger['charger_name']} ({charger['charge_type']}, 이용가능: {charger['is_available']})")
        print()

