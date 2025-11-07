# parking_data.py
"""
주차장 데이터를 중앙에서 관리하는 모듈
main.py와 gradio_parking_app.py에서 공통으로 사용

데이터 구조: (주차장명, 총공간수, 주소, 유형)
- 유형: "무료" 또는 "유료"
"""

# 주차장 데이터 구조: (주차장명, 총공간수, 주소, 유형, 가격정보, 전기차충전소정보)
# CSV 파일에서 읽어온 데이터 (2025-06-25, 2025-08-28 기준)
# 전기차 충전소 정보는 load_ev_charger_data()로 자동 로드됨
DONGS_DATA = [
    ("금곡동", [
        ("매산뜰 공영주차장", 99, "전남 순천시 금곡동 60-1", "무료", "무료", "🔌X"),
    ]),
    ("동외동", [
        ("성동 공영주차장", 84, "전남 순천시 동외동 83", "유료", "30분 무료 후 30분당 500원", "🔌X"),
        ("강남로 제1공영주차장", 18, "전남 순천시 동외동 100-1", "유료", "30분당 500원", "🔌X"),
    ]),
    ("매곡동", [
        ("의료원로터리 제1공영주차장", 10, "전남 순천시 매곡동 127-9", "유료", "30분당 500원", "🔌X"),
    ]),
    ("연향동", [
        ("금당 제2공영주차장", 25, "전남 순천시 연향동 1457", "무료", "무료", "🔌X"),
        ("금당 제3공영주차장", 31, "전남 순천시 연향동 1474", "무료", "무료", "🔌X"),
        ("금당 제4공영주차장", 30, "전남 순천시 연향동 1490", "무료", "무료", "🔌X"),
        ("연향3지구 제1공영주차장", 21, "전남 순천시 연향동 1686-6", "무료", "무료", "🔌O(급속 1개)"),
        ("연향3지구 제2공영주차장", 21, "전남 순천시 연향동 1690-4", "무료", "무료", "🔌X"),
        ("연향 제1공영주차장", 62, "전남 순천시 연향동 1325-2", "유료", "30분당 500원", "🔌X"),
        ("연향 제2공영주차장", 17, "전남 순천시 연향동 1423", "유료", "30분당 500원", "🔌X"),
        ("연향 제3공영주차장", 25, "전남 순천시 연향동 1423", "유료", "30분당 500원", "🔌X"),
        ("연향 제4공영주차장", 27, "전남 순천시 연향동 1423", "유료", "30분당 500원", "🔌X"),
        ("연향 제5공영주차장", 19, "전남 순천시 연향동 1423", "유료", "30분당 500원", "🔌X"),
        ("연향 제6공영주차장", 14, "전남 순천시 연향동 1416", "유료", "30분당 500원", "🔌X"),
        ("연향 제7공영주차장", 42, "전남 순천시 연향동 1431", "유료", "30분당 500원", "🔌X"),
        ("동부 제1공영주차장", 14, "전남 순천시 연향동 1336-2", "유료", "30분당 500원", "🔌X"),
        ("동부 제2공영주차장", 24, "전남 순천시 연향동 1344", "유료", "30분당 500원", "🔌X"),
        ("동부 제3공영주차장", 19, "전남 순천시 연향동 1347", "유료", "30분당 500원", "🔌X"),
        ("동부 제4공영주차장", 10, "전남 순천시 연향동 1423", "유료", "30분당 500원", "🔌X"),
        ("연향주차타워", 81, "전남 순천시 연향동 1320-5", "유료", "30분 무료 후 30분당 500원", "🔌X"),
    ]),
    ("왕지동", [
        ("왕지 제1공영주차장", 136, "전남 순천시 왕지동 852-1", "유료", "1시간 무료 후 30분당 500원", "🔌O(급속 1개)"),
        ("왕지 제2공영주차장", 125, "전남 순천시 왕지동 853-2", "유료", "1시간 무료 후 30분당 500원", "🔌O(급속 1개)"),
    ]),
    ("인제동", [
        ("남정저류지 공영주차장", 68, "전남 순천시 인제동 376-8", "무료", "무료", "🔌X"),
    ]),
    ("장천동", [
        ("시민 공영주차장", 52, "전남 순천시 장천동 234", "유료", "1시간 무료 후 30분당 500원", "🔌X"),
    ]),
    ("조곡동", [
        ("역전로터리 공영주차장", 21, "전남 순천시 조곡동 159-4", "유료", "30분당 500원", "🔌X"),
        ("역전 제3공영주차장", 19, "전남 순천시 조곡동 161-9", "유료", "30분 무료 후 30분당 500원", "🔌X"),
    ]),
    ("조례동", [
        ("호수공원 주차장", 60, "전남 순천시 조례동 1866, 호수공원 옆", "무료", "무료", "🔌X"),
        ("호수공원 자율주차장1", 50, "전남 순천시 왕지2길 13-12, 호수공원 주차장 건너편", "무료", "무료", "🔌X"),
        ("호수공원 자율주차장2", 10, "전남 순천시 왕지4길 13-10, 카페 드로잉 건너편", "무료", "무료", "🔌X"),
        ("호수공원 자율주차장3", 30, "전남 순천시 왕지4길 14-8 1, 카페 소나무 옆", "무료", "무료", "🔌X"),
        ("수매골 공영주차장", 54, "전남 순천시 조례동 1807", "무료", "무료", "🔌O(급속 1개)"),
        ("왕조2동 공영주차장", 67, "전남 순천시 조례동 1824", "유료", "1시간 무료 후 30분당 500원", "🔌X"),
        ("조례 제1공영주차장", 43, "전남 순천시 조례동 1722-8", "유료", "30분당 500원", "🔌X"),
        ("금당 제1공영주차장", 69, "전남 순천시 조례동 1605-1", "유료", "1시간 무료 후 30분당 500원", "🔌X"),
        ("조례 제2공영주차장", 15, "전남 순천시 조례동 1249-3", "유료", "30분당 500원", "🔌X"),
        ("신월 공영주차장", 75, "전남 순천시 조례동 1114", "무료", "무료", "🔌O(급속 1개)"),
        ("금당 공영주차장", 61, "전남 순천시 조례동 1605-1", "무료", "무료", "🔌X"),
    ]),
    ("석현동", [
        ("공과대학 3호관 주차장", 35, "전남 순천시 석현동 375, 공과대학 3호관", "유료", "최초 30분 무료, 그후 30분당 500원", "🔌X"),
        ("공과대학 2호관 주차장", 30, "전남 순천시 석현동 337, 공과대학 2호관", "유료", "최초 30분 무료, 그후 30분당 500원", "🔌X"),
        ("공과대학 1호관 주차장", 45, "전남 순천시 석현동 284, 공과대학 1호관", "유료", "최초 30분 무료, 그후 30분당 500원", "🔌X"),
        ("문화건강센터 수영장",139, "전남 순천시 석현동 35-10", "유료", "최초 2시간30분 무료, 그후 30분당 500원","🔌O(급속 3개)"),
        ("문화센터 주차장",89, "전남 순천시 석현동 35-6", "유료", "최초 2시간30분 무료, 그후 30분당 500원","🔌X")
    ]),
    ("중앙동", [
        ("강남로 제2공영주차장", 14, "전남 순천시 중앙동 40", "유료", "30분당 500원", "🔌X"),
    ]),
    ("행동", [
        ("의료원로터리 제2공영주차장", 8, "전남 순천시 행동 1번지", "유료", "30분당 500원", "🔌X"),
    ]),
]

def get_dongs_data():
    """
    주차장 데이터를 반환합니다.
    
    Returns:
        list: 동별 주차장 데이터 리스트
        구조: [("동이름", [("주차장명", 총공간수, "주소", "유형"), ...]), ...]
    """
    return DONGS_DATA

def add_parking_lot(dong_name: str, lot_name: str, total_spaces: int, address: str, parking_type: str):
    """
    새로운 주차장을 데이터에 추가합니다.
    
    Args:
        dong_name: 동 이름
        lot_name: 주차장 이름
        total_spaces: 총 주차 공간 수
        address: 주차장 주소
        parking_type: 주차장 유형 ("무료" 또는 "유료")
        
    Returns:
        bool: 추가 성공 시 True, 실패 시 False
    """
    if parking_type not in ["무료", "유료"]:
        print(f"❌ 잘못된 주차장 유형: {parking_type} (무료 또는 유료여야 함)")
        return False
    
    # 동이 이미 존재하는지 확인
    dong_found = False
    for i, (existing_dong_name, lots) in enumerate(DONGS_DATA):
        if existing_dong_name == dong_name:
            # 기존 동에 주차장 추가
            DONGS_DATA[i][1].append((lot_name, total_spaces, address, parking_type))
            dong_found = True
            break
    
    if not dong_found:
        # 새로운 동 생성
        DONGS_DATA.append((dong_name, [(lot_name, total_spaces, address, parking_type)]))
    
    print(f"✅ 주차장 '{lot_name}'이 '{dong_name}'에 추가되었습니다.")
    return True

def remove_parking_lot(dong_name: str, lot_name: str):
    """
    주차장을 데이터에서 제거합니다.
    
    Args:
        dong_name: 동 이름
        lot_name: 주차장 이름
        
    Returns:
        bool: 제거 성공 시 True, 실패 시 False
    """
    for i, (existing_dong_name, lots) in enumerate(DONGS_DATA):
        if existing_dong_name == dong_name:
            for j, (existing_lot_name, _, _, _) in enumerate(lots):
                if existing_lot_name == lot_name:
                    DONGS_DATA[i][1].pop(j)
                    print(f"✅ 주차장 '{lot_name}'이 '{dong_name}'에서 제거되었습니다.")
                    return True
    
    print(f"❌ 주차장 '{lot_name}'을 '{dong_name}'에서 찾을 수 없습니다.")
    return False

def get_parking_lots_by_type(parking_type: str):
    """
    특정 유형의 주차장 목록을 반환합니다.
    
    Args:
        parking_type: 주차장 유형 ("무료" 또는 "유료")
        
    Returns:
        list: 해당 유형의 주차장 정보 리스트
    """
    if parking_type not in ["무료", "유료"]:
        print(f"❌ 잘못된 주차장 유형: {parking_type}")
        return []
    
    filtered_lots = []
    for dong_name, lots in DONGS_DATA:
        for lot_name, total_spaces, address, lot_type, price_info, charger_info in lots:
            if lot_type == parking_type:
                filtered_lots.append({
                    'dong_name': dong_name,
                    'lot_name': lot_name,
                    'total_spaces': total_spaces,
                    'address': address,
                    'parking_type': lot_type,
                    'price_info': price_info,
                    'charger_info': charger_info
                })
    
    return filtered_lots

def get_all_parking_lots():
    """
    모든 주차장 정보를 반환합니다.
    
    Returns:
        list: 모든 주차장 정보 리스트
    """
    all_lots = []
    for dong_name, lots in DONGS_DATA:
        for lot_name, total_spaces, address, parking_type, price_info, charger_info in lots:
            all_lots.append({
                'dong_name': dong_name,
                'lot_name': lot_name,
                'total_spaces': total_spaces,
                'address': address,
                'parking_type': parking_type,
                'price_info': price_info
            })
    
    return all_lots

def get_dong_names():
    """
    등록된 모든 동 이름을 반환합니다.
    
    Returns:
        list: 동 이름 리스트
    """
    return [dong_name for dong_name, _ in DONGS_DATA]

def get_lot_count():
    """
    전체 주차장 개수를 반환합니다.
    
    Returns:
        int: 전체 주차장 개수
    """
    total_count = 0
    for _, lots in DONGS_DATA:
        total_count += len(lots)
    return total_count

def get_dong_count():
    """
    등록된 동 개수를 반환합니다.
    
    Returns:
        int: 동 개수
    """
    return len(DONGS_DATA)

# 데이터 검증 함수
def validate_data():
    """
    데이터의 유효성을 검증합니다.
    
    Returns:
        bool: 모든 데이터가 유효하면 True, 그렇지 않으면 False
    """
    for dong_name, lots in DONGS_DATA:
        if not dong_name or not isinstance(dong_name, str):
            print(f"❌ 잘못된 동 이름: {dong_name}")
            return False
        
        for lot_name, total_spaces, address, parking_type, price_info, charger_info in lots:
            if not lot_name or not isinstance(lot_name, str):
                print(f"❌ 잘못된 주차장 이름: {lot_name}")
                return False
            
            if not isinstance(total_spaces, int) or total_spaces <= 0:
                print(f"❌ 잘못된 주차 공간 수: {total_spaces}")
                return False
            
            if not address or not isinstance(address, str):
                print(f"❌ 잘못된 주소: {address}")
                return False
            
            if parking_type not in ["무료", "유료"]:
                print(f"❌ 잘못된 주차장 유형: {parking_type}")
                return False
            
            if not price_info or not isinstance(price_info, str):
                print(f"❌ 잘못된 가격 정보: {price_info}")
                return False
            
            if not charger_info or not isinstance(charger_info, str):
                print(f"❌ 잘못된 전기차 충전소 정보: {charger_info}")
                return False
    
    print("모든 데이터가 유효합니다.")
    return True

if __name__ == "__main__":
    # 테스트 코드
    print("=== 주차장 데이터 테스트 ===")
    print(f"등록된 동: {get_dong_count()}개")
    print(f"전체 주차장: {get_lot_count()}개")
    print(f"동 목록: {get_dong_names()}")
    
    print("\n=== 무료 주차장 목록 ===")
    free_lots = get_parking_lots_by_type("무료")
    for lot in free_lots:
        print(f"- {lot['lot_name']} ({lot['dong_name']})")
    
    print("\n=== 유료 주차장 목록 ===")
    paid_lots = get_parking_lots_by_type("유료")
    for lot in paid_lots:
        print(f"- {lot['lot_name']} ({lot['dong_name']})")
    
    print("\n=== 데이터 검증 ===")
    validate_data()

# ==================== 전기차 충전소 관련 함수 ====================

# 전기차 충전소 데이터 (CSV에서 자동 생성)
EV_CHARGER_DATA = {}

def load_ev_charger_data():
    """
    전기차 충전소 데이터를 로드합니다.
    
    Returns:
        dict: 주차장별 충전소 정보
    """
    global EV_CHARGER_DATA
    
    try:
        from extract_ev_charger_data import read_ev_charger_csv, match_charger_to_parking_lot
        
        csv_path = r"c:\Users\user\Downloads\전라남도 순천시_전기차 충전소 현황_20241127.csv"
        chargers = read_ev_charger_csv(csv_path)
        matched = match_charger_to_parking_lot(chargers, DONGS_DATA)
        
        EV_CHARGER_DATA = matched
        return matched
    except Exception as e:
        print(f"❌ 전기차 충전소 데이터 로드 실패: {e}")
        EV_CHARGER_DATA = {}
        return {}

def get_ev_charger_info(lot_name: str):
    """
    주차장의 전기차 충전소 정보를 반환합니다.
    
    Args:
        lot_name: 주차장 이름
        
    Returns:
        dict: 충전소 정보 또는 None
    """
    if not EV_CHARGER_DATA:
        load_ev_charger_data()
    
    return EV_CHARGER_DATA.get(lot_name)

def get_parking_lots_with_chargers():
    """
    전기차 충전소가 있는 주차장 목록을 반환합니다.
    
    Returns:
        list: 충전소가 있는 주차장 정보 리스트
    """
    if not EV_CHARGER_DATA:
        load_ev_charger_data()
    
    lots_with_chargers = []
    for dong_name, lots in DONGS_DATA:
        for lot_name, total_spaces, address, parking_type, price_info, charger_info_text in lots:
            charger_info = EV_CHARGER_DATA.get(lot_name)
            if charger_info and charger_info.get('has_charger'):
                lots_with_chargers.append({
                    'dong_name': dong_name,
                    'lot_name': lot_name,
                    'total_spaces': total_spaces,
                    'address': address,
                    'parking_type': parking_type,
                    'price_info': price_info,
                    'charger_info': charger_info
                })
    return lots_with_chargers

def get_dongs_with_chargers():
    """
    전기차 충전소가 있는 동 목록을 반환합니다.
    
    Returns:
        list: 충전소가 있는 동 이름 리스트 (중복 제거, 정렬됨)
    """
    if not EV_CHARGER_DATA:
        load_ev_charger_data()
    
    lots_with_chargers = get_parking_lots_with_chargers()
    dongs = list(set([lot['dong_name'] for lot in lots_with_chargers]))
    return sorted(dongs)

def get_ev_charger_lots_by_dong(dong_name: str):
    """
    특정 동의 전기차 충전소가 있는 주차장 목록을 반환합니다.
    
    Args:
        dong_name: 동 이름
        
    Returns:
        list: 충전소가 있는 주차장 이름 리스트
    """
    if not EV_CHARGER_DATA:
        load_ev_charger_data()
    
    lots_with_chargers = get_parking_lots_with_chargers()
    return [lot['lot_name'] for lot in lots_with_chargers if lot['dong_name'] == dong_name]
