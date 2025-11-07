# main.py
"""
주차장 관리 시스템 - 단순화 버전

사용자가 원하는 핵심 기능:
1. 동 선택 → 주차장 선택 → 상태 확인 (랜덤 변화)
2. 시뮬레이션 실행 (전체 시스템 초기화)
"""

import time
import logging
import sys
from typing import Optional

# parking_classes.py 파일에서 우리가 만든 클래스들을 가져옵니다.
from parking_classes import ParkingLot, Dong, ParkingManager

# ==================== 설정 ====================
# 시뮬레이션 설정
SIMULATION_CYCLES = 5  # 시뮬레이션 실행 횟수
CYCLE_INTERVAL = 2     # 사이클 간격 (초)

# 로깅 설정
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# 콘솔에 로그 출력 여부 (False: 파일에만 저장, True: 콘솔과 파일 모두)
CONSOLE_LOGGING = False

# ==================== 로깅 설정 ====================
def setup_logging() -> None:
    """
    로깅 시스템을 설정합니다.
    """
    # 핸들러 리스트 생성
    handlers = [logging.FileHandler('parking_system.log', encoding='utf-8')]
    
    # 콘솔 로깅이 활성화된 경우에만 StreamHandler 추가
    if CONSOLE_LOGGING:
        handlers.append(logging.StreamHandler(sys.stdout))
    
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=handlers
    )
    logger = logging.getLogger(__name__)
    logger.info("주차장 관리 시스템 시작")

# ==================== 시스템 초기화 ====================
def initialize_system() -> ParkingManager:
    """
    주차장 관리 시스템을 초기화합니다.
    
    Returns:
        ParkingManager: 초기화된 관리자 객체
        
    Raises:
        Exception: 시스템 초기화 실패 시
    """
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
    """
    주차장 데이터를 설정합니다.
    
    Args:
        manager: 주차장 관리자 객체
        
    Returns:
        bool: 설정 성공 시 True, 실패 시 False
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("주차장 데이터 설정 시작")
        
        # 1. 동 지역 추가 (주차장명, 총공간수, 상세주소)
        dongs_data = [
            ("조례동", [
                ("호수공원 주차장", 60, "전남 순천시 조례동 1866, 호수공원 옆"),
                ("호수공원 자율주차장1", 50, "전남 순천시 왕지2길 13-12, 호수공원 주차장 건너편"),
                ("호수공원 자율주차장2", 10, "전남 순천시 왕지4길 13-10, 카페 드로잉 건너편"),
                ("호수공원 자율주차장3", 30, "전남 순천시 왕지4길 14-8 1, 카페 소나무 옆")
            ]),
            ("석현동", [
                ("공과대학 3호관 주차장", 35, "전남 순천시 중앙로 255, 공과대학 3호관"),
                ("공과대학 2호관 주차장", 30, "전남 순천시 중앙로 255, 공과대학 2호관"),
                ("공과대학 1호관 주차장", 45, "전남 순천시 중앙로 255, 공과대학 1호관")
            ])
        ]
        
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
            for lot_name, total_spaces, address in lots_data:
                try:
                    lot = ParkingLot(lot_name, total_spaces, address)
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

# ==================== 관리자용 시뮬레이션 (숨김) ====================
def run_simulation(manager: ParkingManager, cycles: int = SIMULATION_CYCLES, interval: float = CYCLE_INTERVAL) -> None:
    """
    주차장 시뮬레이션을 실행합니다. (관리자용 기능)
    
    Args:
        manager: 주차장 관리자 객체
        cycles: 시뮬레이션 실행 횟수
        interval: 사이클 간격 (초)
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"시뮬레이션 시작: {cycles}회 실행, {interval}초 간격")
        
        for i in range(cycles):
            logger.info(f"시뮬레이션 사이클 {i+1}/{cycles} 시작")
            
            # 모든 주차장 상태 업데이트
            manager.update_all_lots()
            
            # 전체 현황 출력
            manager.display_all_status()
            
            # 마지막 사이클이 아니면 대기
            if i < cycles - 1:
                logger.info(f"{interval}초 대기 중...")
                time.sleep(interval)
        
        logger.info("시뮬레이션 완료")
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 시뮬레이션 중단됨")
    except Exception as e:
        logger.error(f"시뮬레이션 실행 중 오류 발생: {e}")

# ==================== 사용자 메뉴 ====================
def show_menu() -> None:
    """
    사용자 메뉴를 출력합니다.
    """
    print("\n" + "="*40)
    print("🚗 주차장 관리 시스템")
    print("="*40)
    print("1. 주차장 현황 확인")
    print("2. 종료")
    print("="*40)

def get_user_choice() -> str:
    """
    사용자 선택을 받습니다.
    
    Returns:
        str: 사용자 선택
    """
    while True:
        try:
            choice = input("선택하세요 (1-2): ").strip()
            if choice in ['1', '2']:
                return choice
            else:
                print("❌ 잘못된 선택입니다. 1-2 중에서 선택해주세요.")
        except KeyboardInterrupt:
            print("\n👋 프로그램을 종료합니다.")
            sys.exit(0)
        except Exception as e:
            print(f"❌ 입력 오류: {e}")

# ==================== 통합된 주차장 현황 확인 ====================
def check_parking_status(manager: ParkingManager) -> None:
    """
    통합된 주차장 현황 확인 기능
    
    사용자 플로우:
    1. 동 선택 (목적지 설정)
    2. 해당 동의 모든 주차장 현황 표시
    3. 관심 있는 주차장 선택 (선택사항)
    4. 실시간 변화 확인 (선택사항)
    """
    logger = logging.getLogger(__name__)
    
    print("\n🔍 주차장 현황 확인")
    print("목적지 동을 선택하고 주차장 현황을 확인할 수 있습니다.")
    
    try:
        # 1단계: 동 선택 (목적지 설정)
        selected_dong = select_dong(manager)
        if not selected_dong:
            print("❌ 동 선택이 취소되었습니다.")
            return
        
        # 2단계: 해당 동의 모든 주차장 현황 표시
        print(f"\n" + "="*60)
        print(f"🏘️ {selected_dong.name} 주차장 현황")
        print("="*60)
        
        lot_names = selected_dong.get_lot_names()
        if not lot_names:
            print(f"❌ '{selected_dong.name}'에 등록된 주차장이 없습니다.")
            return
        
        # 모든 주차장 현황 표시
        for i, lot_name in enumerate(lot_names, 1):
            lot = selected_dong.get_lot_by_name(lot_name)
            if lot:
                occupancy_rate = lot.get_occupancy_rate()
                available_spaces = lot.get_available_spaces()
                
                print(f"{i}. {lot_name}")
                print(f"   📍 {lot.location_info}")
                print(f"   🚗 {lot.current_cars}/{lot.total_spaces} ({occupancy_rate:.1%})")
                print(f"   🆓 여유: {available_spaces}개")
                
                # 간단한 시각적 표시
                visual_bar = '█' * int(occupancy_rate * 15) + '░' * (15 - int(occupancy_rate * 15))
                print(f"   📊 {visual_bar} {occupancy_rate:.1%}")
                print()
        
        print("="*60)
        logger.info(f"동 '{selected_dong.name}' 주차장 현황 출력 완료")
        
        # 3단계: 관심 있는 주차장 상세 확인 (선택사항)
        print("\n💡 관심 있는 주차장의 상세 정보를 확인하시겠습니까?")
        print("(Enter: 상세 확인, 'q': 종료)")
        
        while True:
            try:
                user_input = input("\n선택하세요 (Enter/q): ").strip().lower()
                
                if user_input == 'q':
                    print("👋 현황 확인을 종료합니다.")
                    break
                
                # 주차장 선택
                selected_lot = select_parking_lot(selected_dong)
                if not selected_lot:
                    print("❌ 주차장 선택이 취소되었습니다.")
                    continue
                
                # 4단계: 실시간 변화 확인
                print(f"\n🅿️ '{selected_lot.name}' 상세 정보")
                print("(Enter: 상태 업데이트, 'q': 종료)")
                
                while True:
                    try:
                        detail_input = input("\n명령을 입력하세요 (Enter/q): ").strip().lower()
                        
                        if detail_input == 'q':
                            print("👋 상세 확인을 종료합니다.")
                            break
                        
                        # 주차장 상태 랜덤 업데이트
                        print("\n🔄 주차장 상태 업데이트 중...")
                        update_result = selected_lot.update_vehicle_count()
                        
                        # 변화 알림 (실제 변화량 표시)
                        change = update_result['change']
                        if update_result['action'] == "진입":
                            print(f"🚗 차량 {change}대 진입!")
                        elif update_result['action'] == "출차":
                            print(f"🚙 차량 {abs(change)}대 출차!")
                        else:
                            print("⏸️ 변화 없음")
                        
                        # 주차장 상세 상태 출력
                        display_lot_status(selected_lot)
                        
                        logger.info(f"주차장 '{selected_lot.name}' 상태 확인: {update_result['action']}")
                        
                    except KeyboardInterrupt:
                        print("\n👋 상세 확인을 종료합니다.")
                        break
                    except Exception as e:
                        logger.error(f"상세 확인 중 오류 발생: {e}")
                        print(f"❌ 오류가 발생했습니다: {e}")
                
            except KeyboardInterrupt:
                print("\n👋 현황 확인을 종료합니다.")
                break
            except Exception as e:
                logger.error(f"현황 확인 중 오류 발생: {e}")
                print(f"❌ 오류가 발생했습니다: {e}")
        
    except Exception as e:
        logger.error(f"주차장 현황 확인 실행 중 오류 발생: {e}")
        print(f"❌ 오류가 발생했습니다: {e}")

# ==================== 헬퍼 함수들 ====================
def select_dong(manager: ParkingManager) -> Optional['Dong']:
    """
    사용자가 동을 선택할 수 있도록 도와줍니다.
    
    Args:
        manager: 주차장 관리자 객체
        
    Returns:
        Optional[Dong]: 선택된 동 객체 또는 None
    """
    logger = logging.getLogger(__name__)
    
    try:
        # 등록된 동 목록 가져오기
        dong_names = manager.get_dong_names()
        
        if not dong_names:
            print("❌ 등록된 동이 없습니다.")
            return None
        
        # 동 목록 출력
        print("\n" + "="*30)
        print("🏘️ 동 선택")
        print("="*30)
        for i, dong_name in enumerate(dong_names, 1):
            dong = manager.get_dong(dong_name)
            if dong:
                lot_count = dong.get_total_lots()
                print(f"{i}. {dong_name} (주차장 {lot_count}개)")
        
        # 사용자 선택 받기
        while True:
            try:
                choice = input(f"\n동을 선택하세요 (1-{len(dong_names)}): ").strip()
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(dong_names):
                    selected_dong_name = dong_names[choice_num - 1]
                    selected_dong = manager.get_dong(selected_dong_name)
                    print(f"✅ '{selected_dong_name}' 선택됨")
                    logger.info(f"사용자가 동 '{selected_dong_name}' 선택")
                    return selected_dong
                else:
                    print(f"❌ 1-{len(dong_names)} 범위에서 선택해주세요.")
                    
            except ValueError:
                print("❌ 숫자를 입력해주세요.")
            except KeyboardInterrupt:
                print("\n👋 선택을 취소합니다.")
                return None
                
    except Exception as e:
        logger.error(f"동 선택 중 오류 발생: {e}")
        print(f"❌ 오류가 발생했습니다: {e}")
        return None

def select_parking_lot(dong: 'Dong') -> Optional['ParkingLot']:
    """
    사용자가 주차장을 선택할 수 있도록 도와줍니다.
    
    Args:
        dong: 선택된 동 객체
        
    Returns:
        Optional[ParkingLot]: 선택된 주차장 객체 또는 None
    """
    logger = logging.getLogger(__name__)
    
    try:
        # 등록된 주차장 목록 가져오기
        lot_names = dong.get_lot_names()
        
        if not lot_names:
            print(f"❌ '{dong.name}'에 등록된 주차장이 없습니다.")
            return None
        
        # 주차장 목록 출력
        print(f"\n" + "="*50)
        print(f"🅿️ {dong.name} 주차장 선택")
        print("="*50)
        for i, lot_name in enumerate(lot_names, 1):
            lot = dong.get_lot_by_name(lot_name)
            if lot:
                occupancy_rate = lot.get_occupancy_rate()
                available_spaces = lot.get_available_spaces()
                print(f"{i}. {lot_name}")
                print(f"   📍 주소: {lot.location_info}")
                print(f"   🚗 현재: {lot.current_cars}/{lot.total_spaces} ({occupancy_rate:.1%})")
                print(f"   🆓 여유: {available_spaces}개")
                print()
        
        # 사용자 선택 받기
        while True:
            try:
                choice = input(f"주차장을 선택하세요 (1-{len(lot_names)}): ").strip()
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(lot_names):
                    selected_lot_name = lot_names[choice_num - 1]
                    selected_lot = dong.get_lot_by_name(selected_lot_name)
                    print(f"✅ '{selected_lot_name}' 선택됨")
                    logger.info(f"사용자가 주차장 '{selected_lot_name}' 선택")
                    return selected_lot
                else:
                    print(f"❌ 1-{len(lot_names)} 범위에서 선택해주세요.")
                    
            except ValueError:
                print("❌ 숫자를 입력해주세요.")
            except KeyboardInterrupt:
                print("\n👋 선택을 취소합니다.")
                return None
                
    except Exception as e:
        logger.error(f"주차장 선택 중 오류 발생: {e}")
        print(f"❌ 오류가 발생했습니다: {e}")
        return None

def display_lot_status(lot: 'ParkingLot') -> None:
    """
    주차장의 상태를 출력합니다.
    
    Args:
        lot: 주차장 객체
    """
    logger = logging.getLogger(__name__)
    
    try:
        print("\n" + "="*50)
        print(f"🅿️ {lot.name}")
        print("="*50)
        
        # 기본 정보
        print(f"📍 주소: {lot.location_info}")
        print(f"📊 총 주차 공간: {lot.total_spaces}개")
        print(f"🚗 현재 주차된 차량: {lot.current_cars}대")
        print(f"🆓 사용 가능한 공간: {lot.get_available_spaces()}개")
        
        # 점유율 정보
        occupancy_rate = lot.get_occupancy_rate()
        print(f"📈 점유율: {occupancy_rate:.1%}")
        
        # 상태 정보
        if lot.is_full():
            print("🔴 상태: 가득 참")
        elif lot.is_empty():
            print("🟢 상태: 비어있음")
        else:
            print("🟡 상태: 부분 점유")
        
        # 간단한 시각적 표시
        print(f"\n📊 현황: {'█' * int(occupancy_rate * 20)}{'░' * (20 - int(occupancy_rate * 20))} {occupancy_rate:.1%}")
        
        print("="*50)
        logger.info(f"주차장 '{lot.name}' 상태 출력 완료")
        
    except Exception as e:
        logger.error(f"주차장 상태 출력 실패: {e}")
        print(f"❌ 현황 출력 중 오류가 발생했습니다: {e}")


# ==================== 메인 함수 ====================
def main() -> None:
    """
    메인 실행 함수입니다.
    """
    # 로깅 설정
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 시스템 초기화
        manager = initialize_system()
        
        # 데이터 설정
        if not setup_parking_data(manager):
            logger.error("데이터 설정 실패로 프로그램을 종료합니다.")
            return
        
        # 사용자 메뉴 루프
        while True:
            show_menu()
            choice = get_user_choice()
            
            if choice == '1':
                # 통합된 주차장 현황 확인
                check_parking_status(manager)
                
            elif choice == '2':
                # 종료
                print("👋 주차장 관리 시스템을 종료합니다.")
                logger.info("프로그램 종료")
                break
                
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류 발생: {e}")
        print(f"❌ 오류가 발생했습니다: {e}")
    finally:
        print("프로그램이 종료되었습니다.")

# ==================== 실행 코드 ====================
if __name__ == "__main__":
    main()