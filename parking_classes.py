# parking_classes.py
"""
주차장 관리 시스템의 핵심 클래스들을 정의하는 모듈

이 모듈은 다음과 같은 클래스들을 포함합니다:
- ParkingManager: 전체 동 지역을 관리하는 최상위 클래스
- Dong: 개별 동 지역을 관리하는 중간 관리자 클래스  
- ParkingLot: 개별 주차장을 관리하는 기본 단위 클래스

각 클래스는 계층적 구조를 가지며, 상위 클래스가 하위 클래스들을 관리하는
패턴으로 설계되었습니다.
"""

import random
from typing import Dict, List, Optional
import logging

# 로깅 설정: 콘솔 출력 비활성화 (파일만 저장)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('parking_system.log', encoding='utf-8')]
)

# ==================== 상수 정의 ====================
# 차량 진입 확률 (0.0 ~ 1.0 사이의 값)
# 이 값이 높을수록 차량이 더 자주 들어옴
DEFAULT_ENTRY_PROBABILITY = 0.4

# 차량 출차 확률 (0.0 ~ 1.0 사이의 값)
# 이 값이 높을수록 차량이 더 자주 나감
DEFAULT_EXIT_PROBABILITY = 0.4

# 차량 진입/출차 최대 수량 (랜덤하게 1~최대값 사이에서 선택)
MAX_VEHICLE_CHANGE = 5

# 주차장의 최소 차량 수 (항상 0 이상이어야 함)
MIN_CARS = 0

class ParkingManager:
    """
    전체 '동' 지역을 관리하는 클래스 (총괄 관리자).
    가장 상위의 제어 객체입니다.
    
    이 클래스는 여러 개의 동(Dong) 객체들을 관리하며, 각 동에 속한 주차장들의
    상태를 통합적으로 모니터링하고 제어하는 역할을 담당합니다.
    
    Attributes:
        dongs (Dict[str, 'Dong']): 동 이름을 키로 하고 Dong 객체를 값으로 하는 딕셔너리
        logger (logging.Logger): 로깅을 위한 로거 객체
    """
    def __init__(self) -> None:
        """
        ParkingManager 객체를 초기화합니다.
        
        동 관리용 딕셔너리와 로깅 시스템을 설정합니다.
        """
        # {'동이름': Dong객체} 형태로 관리하여 특정 동을 쉽게 찾을 수 있도록 딕셔너리 사용
        # O(1) 시간복잡도로 동을 검색할 수 있어 효율적
        self.dongs: Dict[str, 'Dong'] = {}
        
        # 즐겨찾기 주차장 관리 (동이름:주차장이름 형태로 저장)
        self.favorites: List[str] = []
        
        # 로깅 시스템 초기화 - 디버깅과 모니터링을 위해 사용
        self.logger = logging.getLogger(__name__)

    def add_dong(self, dong_name: str) -> bool:
        """
        관리 목록에 새로운 Dong 객체를 추가합니다.
        
        동 이름의 유효성을 검사하고, 중복 여부를 확인한 후
        새로운 Dong 객체를 생성하여 관리 목록에 추가합니다.
        
        Args:
            dong_name: 추가할 동의 이름 (비어있지 않은 문자열)
            
        Returns:
            bool: 추가 성공 시 True, 실패 시 False
            
        Example:
            >>> manager = ParkingManager()
            >>> success = manager.add_dong("강남동")
            >>> print(success)  # True
        """
        # 입력값 유효성 검사: None, 빈 문자열, 잘못된 타입 체크
        if not dong_name or not isinstance(dong_name, str):
            self.logger.error(f"잘못된 동 이름: {dong_name}")
            return False
            
        # 중복 추가 방지: 이미 존재하는 동인지 확인
        if dong_name in self.dongs:
            self.logger.warning(f"동 '{dong_name}'이 이미 존재함")
            return False
            
        try:
            # 새로운 Dong 객체 생성 및 딕셔너리에 추가
            new_dong = Dong(dong_name)
            self.dongs[dong_name] = new_dong
            self.logger.info(f"새로운 동 '{dong_name}' 추가됨")
            return True
        except Exception as e:
            # Dong 객체 생성 실패 시 예외 처리
            self.logger.error(f"동 '{dong_name}' 추가 실패: {e}")
            return False

    def get_dong(self, dong_name: str) -> Optional['Dong']:
        """
        이름으로 특정 Dong 객체를 찾아 반환합니다.
        
        딕셔너리의 get() 메서드를 사용하여 O(1) 시간복잡도로
        동 객체를 검색합니다. 존재하지 않는 경우 None을 반환합니다.
        
        Args:
            dong_name: 찾을 동의 이름
            
        Returns:
            Optional[Dong]: 찾은 Dong 객체 또는 None (존재하지 않는 경우)
            
        Example:
            >>> manager = ParkingManager()
            >>> manager.add_dong("강남동")
            >>> dong = manager.get_dong("강남동")
            >>> print(dong.name)  # "강남동"
        """
        # 입력값 유효성 검사
        if not dong_name or not isinstance(dong_name, str):
            self.logger.error(f"잘못된 동 이름: {dong_name}")
            return None
            
        # 딕셔너리에서 동 객체 검색 (O(1) 시간복잡도)
        dong = self.dongs.get(dong_name)
        
        # 검색 결과 로깅
        if dong is None:
            self.logger.warning(f"동 '{dong_name}'을 찾을 수 없음")
        else:
            self.logger.debug(f"동 '{dong_name}' 검색 성공")
            
        return dong

    def update_all_lots(self) -> None:
        """
        관리하는 모든 '동'에 상태 업데이트 명령을 내립니다.
        
        등록된 모든 동의 주차장 상태를 일괄 업데이트합니다.
        각 동의 업데이트 과정에서 발생하는 예외를 개별적으로 처리하여
        하나의 동에서 오류가 발생해도 다른 동의 업데이트는 계속 진행됩니다.
        
        Returns:
            None
            
        Note:
            이 메서드는 모든 동의 주차장 상태를 시뮬레이션으로 업데이트합니다.
            실제 운영 환경에서는 데이터베이스나 외부 API와 연동될 수 있습니다.
        """
        self.logger.info("모든 주차장 상태 업데이트 시작")
        updated_count = 0
        
        # 모든 동에 대해 순차적으로 업데이트 수행
        for dong in self.dongs.values():
            try:
                # 각 동의 주차장 상태 업데이트
                dong.update_lots_in_dong()
                updated_count += 1
            except Exception as e:
                # 개별 동 업데이트 실패 시 로깅하고 계속 진행
                self.logger.error(f"동 '{dong.name}' 업데이트 실패: {e}")
                
        # 업데이트 완료 통계 로깅
        self.logger.info(f"주차장 상태 업데이트 완료: {updated_count}/{len(self.dongs)} 동 처리됨")

    def display_all_status(self) -> None:
        """
        관리하는 모든 '동'에 현황 출력 명령을 내려 전체 정보를 표시합니다.
        
        등록된 모든 동의 주차장 현황을 사용자 친화적인 형태로 출력합니다.
        등록된 동이 없는 경우와 개별 동 출력 실패 시에도 적절한 메시지를 제공합니다.
        
        Returns:
            None
            
        Output Format:
            ======= 전체 주차장 실시간 현황 =======
            총 X개 동이 등록되어 있습니다.
            
            --- 동이름 주차장 현황 ---
            - 주차장명 (위치): 현재차량수 / 총공간수 (점유율%)
            =======================================
        """
        print("\n======= 전체 주차장 실시간 현황 =======")
        
        # 등록된 동이 없는 경우 처리
        if not self.dongs:
            print("등록된 동이 없습니다.")
            self.logger.info("현황 출력: 등록된 동 없음")
        else:
            total_dongs = len(self.dongs)
            print(f"총 {total_dongs}개 동이 등록되어 있습니다.")
            
            # 각 동의 현황을 순차적으로 출력
            for dong in self.dongs.values():
                try:
                    # 각 동의 주차장 현황 출력
                    dong.display_dong_status()
                except Exception as e:
                    # 개별 동 출력 실패 시 오류 메시지 표시
                    self.logger.error(f"동 '{dong.name}' 현황 출력 실패: {e}")
                    print(f"  - {dong.name}: 현황 출력 오류")
                    
            # 출력 완료 통계 로깅
            self.logger.info(f"현황 출력 완료: {total_dongs}개 동 처리됨")
            
        print("=======================================")
    
    def get_total_dongs(self) -> int:
        """
        등록된 동의 총 개수를 반환합니다.
        
        현재 관리하고 있는 동의 총 개수를 반환합니다.
        이는 통계 정보나 시스템 상태 확인에 유용합니다.
        
        Returns:
            int: 등록된 동의 개수 (0 이상의 정수)
            
        Example:
            >>> manager = ParkingManager()
            >>> manager.add_dong("강남동")
            >>> manager.add_dong("서초동")
            >>> count = manager.get_total_dongs()
            >>> print(count)  # 2
        """
        return len(self.dongs)
    
    def get_dong_names(self) -> list[str]:
        """
        등록된 모든 동의 이름 목록을 반환합니다.
        
        현재 관리하고 있는 모든 동의 이름을 리스트 형태로 반환합니다.
        이는 동 목록을 순회하거나 사용자에게 선택지를 제공할 때 유용합니다.
        
        Returns:
            list[str]: 동 이름 목록 (빈 리스트일 수 있음)
            
        Example:
            >>> manager = ParkingManager()
            >>> manager.add_dong("강남동")
            >>> manager.add_dong("서초동")
            >>> names = manager.get_dong_names()
            >>> print(names)  # ['강남동', '서초동']
        """
        return list(self.dongs.keys())
    
    def remove_dong(self, dong_name: str) -> bool:
        """
        등록된 동을 제거합니다.
        
        지정된 이름의 동을 관리 목록에서 제거합니다.
        동이 존재하지 않거나 잘못된 입력값인 경우 실패를 반환합니다.
        
        Args:
            dong_name: 제거할 동의 이름
            
        Returns:
            bool: 제거 성공 시 True, 실패 시 False
            
        Warning:
            동을 제거하면 해당 동에 속한 모든 주차장 정보도 함께 삭제됩니다.
            이 작업은 되돌릴 수 없으므로 신중하게 사용해야 합니다.
            
        Example:
            >>> manager = ParkingManager()
            >>> manager.add_dong("강남동")
            >>> success = manager.remove_dong("강남동")
            >>> print(success)  # True
        """
        # 입력값 유효성 검사
        if not dong_name or not isinstance(dong_name, str):
            self.logger.error(f"잘못된 동 이름: {dong_name}")
            return False
            
        # 존재 여부 확인
        if dong_name not in self.dongs:
            self.logger.warning(f"제거할 동 '{dong_name}'이 존재하지 않음")
            return False
            
        # 동 제거 및 로깅
        del self.dongs[dong_name]
        self.logger.info(f"동 '{dong_name}' 제거됨")
        return True

    def add_favorite(self, dong_name: str, lot_name: str) -> bool:
        """
        즐겨찾기에 주차장을 추가합니다.
        
        Args:
            dong_name: 동 이름
            lot_name: 주차장 이름
            
        Returns:
            bool: 추가 성공 시 True, 실패 시 False
        """
        if not dong_name or not lot_name:
            self.logger.error("동 이름과 주차장 이름이 필요합니다")
            return False
            
        # 주차장 존재 여부 확인
        dong = self.get_dong(dong_name)
        if not dong:
            self.logger.error(f"동 '{dong_name}'을 찾을 수 없습니다")
            return False
            
        lot = dong.get_lot_by_name(lot_name)
        if not lot:
            self.logger.error(f"주차장 '{lot_name}'을 찾을 수 없습니다")
            return False
            
        # 즐겨찾기 키 생성 (동이름:주차장이름)
        favorite_key = f"{dong_name}:{lot_name}"
        
        # 중복 확인
        if favorite_key in self.favorites:
            self.logger.warning(f"'{favorite_key}'이 이미 즐겨찾기에 있습니다")
            return False
            
        # 즐겨찾기 추가
        self.favorites.append(favorite_key)
        self.logger.info(f"'{favorite_key}'이 즐겨찾기에 추가되었습니다")
        return True

    def remove_favorite(self, dong_name: str, lot_name: str) -> bool:
        """
        즐겨찾기에서 주차장을 제거합니다.
        
        Args:
            dong_name: 동 이름
            lot_name: 주차장 이름
            
        Returns:
            bool: 제거 성공 시 True, 실패 시 False
        """
        if not dong_name or not lot_name:
            self.logger.error("동 이름과 주차장 이름이 필요합니다")
            return False
            
        # 즐겨찾기 키 생성
        favorite_key = f"{dong_name}:{lot_name}"
        
        # 즐겨찾기에서 제거
        if favorite_key in self.favorites:
            self.favorites.remove(favorite_key)
            self.logger.info(f"'{favorite_key}'이 즐겨찾기에서 제거되었습니다")
            return True
        else:
            self.logger.warning(f"'{favorite_key}'이 즐겨찾기에 없습니다")
            return False

    def get_favorites(self) -> List[dict]:
        """
        즐겨찾기 주차장 목록을 반환합니다.
        
        Returns:
            List[dict]: 즐겨찾기 주차장 정보 리스트
        """
        favorites_info = []
        
        for favorite_key in self.favorites:
            try:
                dong_name, lot_name = favorite_key.split(":", 1)
                dong = self.get_dong(dong_name)
                
                if dong:
                    lot = dong.get_lot_by_name(lot_name)
                    if lot:
                        # 주차장 정보 수집
                        lot_info = {
                            'dong_name': dong_name,
                            'lot_name': lot_name,
                            'location': lot.location_info,
                            'current_cars': lot.current_cars,
                            'total_spaces': lot.total_spaces,
                            'occupancy_rate': lot.get_occupancy_rate(),
                            'available_spaces': lot.get_available_spaces(),
                            'is_full': lot.is_full(),
                            'is_empty': lot.is_empty()
                        }
                        favorites_info.append(lot_info)
                    else:
                        # 주차장이 삭제된 경우 즐겨찾기에서 제거
                        self.favorites.remove(favorite_key)
                        self.logger.warning(f"삭제된 주차장 '{favorite_key}'을 즐겨찾기에서 제거했습니다")
                else:
                    # 동이 삭제된 경우 즐겨찾기에서 제거
                    self.favorites.remove(favorite_key)
                    self.logger.warning(f"삭제된 동의 주차장 '{favorite_key}'을 즐겨찾기에서 제거했습니다")
                    
            except Exception as e:
                self.logger.error(f"즐겨찾기 정보 처리 중 오류: {e}")
                continue
                
        return favorites_info

    def is_favorite(self, dong_name: str, lot_name: str) -> bool:
        """
        주차장이 즐겨찾기에 있는지 확인합니다.
        
        Args:
            dong_name: 동 이름
            lot_name: 주차장 이름
            
        Returns:
            bool: 즐겨찾기에 있으면 True, 없으면 False
        """
        if not dong_name or not lot_name:
            return False
            
        favorite_key = f"{dong_name}:{lot_name}"
        return favorite_key in self.favorites

    def get_lots_by_type(self, parking_type: str) -> List[dict]:
        """
        특정 유형의 주차장 목록을 반환합니다.
        
        Args:
            parking_type: 주차장 유형 ("무료" 또는 "유료")
            
        Returns:
            List[dict]: 해당 유형의 주차장 정보 리스트
        """
        if parking_type not in ["무료", "유료"]:
            self.logger.error(f"잘못된 주차장 유형: {parking_type}")
            return []
            
        filtered_lots = []
        
        for dong in self.dongs.values():
            for lot in dong.parking_lots:
                if lot.parking_type == parking_type:
                    lot_info = {
                        'dong_name': dong.name,
                        'lot_name': lot.name,
                        'location': lot.location_info,
                        'current_cars': lot.current_cars,
                        'total_spaces': lot.total_spaces,
                        'occupancy_rate': lot.get_occupancy_rate(),
                        'available_spaces': lot.get_available_spaces(),
                        'is_full': lot.is_full(),
                        'is_empty': lot.is_empty(),
                        'parking_type': lot.parking_type,
                        'price_info': lot.price_info
                    }
                    filtered_lots.append(lot_info)
        
        self.logger.info(f"'{parking_type}' 유형 주차장 {len(filtered_lots)}개 조회됨")
        return filtered_lots

class Dong:
    """
    하나의 '동' 지역을 관리하는 클래스 (중간 관리자).
    자신에게 속한 여러 ParkingLot 객체들을 관리합니다.
    
    이 클래스는 특정 동 지역에 속한 모든 주차장들을 관리하며,
    주차장의 추가, 제거, 상태 업데이트 등의 기능을 제공합니다.
    
    Dong 클래스는 ParkingManager와 ParkingLot 사이의 중간 계층으로,
    지역별 주차장 관리를 담당하는 핵심 컴포넌트입니다.
    
    Attributes:
        name (str): 동의 이름 (예: "강남동", "서초동")
        parking_lots (List[ParkingLot]): 해당 동에 속한 주차장 목록
        logger (logging.Logger): 로깅을 위한 로거 객체 (동별로 구분됨)
        
    Example:
        >>> dong = Dong("강남동")
        >>> lot = ParkingLot("강남주차장", 100, "강남역 근처")
        >>> dong.add_lot(lot)
        >>> dong.display_dong_status()
    """
    def __init__(self, name: str) -> None:
        """
        Dong 객체를 초기화합니다.
        
        동의 이름을 검증하고, 주차장 목록과 로깅 시스템을 초기화합니다.
        잘못된 이름이 입력되면 ValueError 예외를 발생시킵니다.
        
        Args:
            name: 동의 이름 (비어있지 않은 문자열)
                - 예: "강남동", "서초동", "마포동" 등
                - None, 빈 문자열, 또는 문자열이 아닌 타입은 허용되지 않음
                
        Raises:
            ValueError: name이 None, 빈 문자열, 또는 문자열이 아닌 경우
            
        Note:
            로거는 동 이름을 포함하여 생성되므로, 로그에서 어떤 동의 작업인지
            쉽게 구분할 수 있습니다.
        """
        # 입력값 유효성 검사: None, 빈 문자열, 잘못된 타입 체크
        if not name or not isinstance(name, str):
            raise ValueError("동 이름은 비어있지 않은 문자열이어야 합니다")
            
        # 동 이름 저장
        self.name = name
        
        # 주차장 목록 초기화 (빈 리스트로 시작)
        self.parking_lots: List['ParkingLot'] = []
        
        # 동별 로거 생성 (로그에서 동을 구분할 수 있도록)
        self.logger = logging.getLogger(f"{__name__}.{name}")

    def add_lot(self, lot: 'ParkingLot') -> bool:
        """
        자신의 관리 목록에 새로운 ParkingLot 객체를 추가합니다.
        
        주차장 객체의 유효성을 검사하고, 중복 여부를 확인한 후
        관리 목록에 추가합니다. 이 메서드는 안전한 주차장 추가를 보장하며,
        모든 작업 과정을 로깅합니다.
        
        Args:
            lot: 추가할 주차장 객체
                - ParkingLot 타입의 객체여야 함
                - None이나 다른 타입의 객체는 거부됨
                
        Returns:
            bool: 추가 성공 시 True, 실패 시 False
                - True: 주차장이 성공적으로 추가됨
                - False: 유효성 검사 실패, 중복, 또는 예외 발생
                
        Example:
            >>> dong = Dong("강남동")
            >>> lot = ParkingLot("강남주차장", 100, "강남역 근처")
            >>> success = dong.add_lot(lot)
            >>> print(success)  # True
            
        Note:
            - 동일한 주차장 객체는 중복으로 추가될 수 없음
            - 추가 성공 시 콘솔과 로그에 모두 메시지 출력
            - 예외 발생 시에도 시스템이 중단되지 않고 False 반환
        """
        # 입력값 유효성 검사: ParkingLot 타입인지 확인
        if not isinstance(lot, ParkingLot):
            self.logger.error(f"잘못된 주차장 객체: {type(lot)}")
            return False
            
        # 중복 추가 방지: 이미 존재하는 주차장인지 확인
        if lot in self.parking_lots:
            self.logger.warning(f"주차장 '{lot.name}'이 이미 존재함")
            return False
            
        try:
            # 주차장을 리스트에 추가
            self.parking_lots.append(lot)
            
            # 성공 로깅 및 사용자 알림
            self.logger.info(f"'{self.name}'에 '{lot.name}'이(가) 추가되었습니다.")
            print(f"'{self.name}'에 '{lot.name}'이(가) 추가되었습니다.")
            return True
            
        except Exception as e:
            # 예외 발생 시 오류 로깅 및 실패 반환
            self.logger.error(f"주차장 '{lot.name}' 추가 실패: {e}")
            return False

    def update_lots_in_dong(self) -> None:
        """
        자신에게 속한 모든 주차장의 상태를 업데이트합니다.
        
        등록된 모든 주차장의 차량 수를 시뮬레이션으로 업데이트합니다.
        각 주차장의 업데이트 과정에서 발생하는 예외를 개별적으로 처리하여
        하나의 주차장에서 오류가 발생해도 다른 주차장의 업데이트는 계속 진행됩니다.
        
        이 메서드는 견고한 오류 처리 메커니즘을 제공하여 시스템의 안정성을 보장합니다.
        
        Returns:
            None
            
        Note:
            - 이 메서드는 주차장 상태를 시뮬레이션으로 업데이트합니다
            - 실제 운영 환경에서는 센서 데이터나 외부 API와 연동될 수 있습니다
            - 개별 주차장 업데이트 실패는 전체 프로세스를 중단시키지 않습니다
            - 모든 작업 과정이 로그에 기록됩니다
            
        Example:
            >>> dong = Dong("강남동")
            >>> dong.update_lots_in_dong()  # 모든 주차장 상태 업데이트
        """
        # 업데이트 시작 로깅
        self.logger.debug(f"'{self.name}' 주차장 상태 업데이트 시작")
        updated_count = 0
        
        # 모든 주차장에 대해 순차적으로 업데이트 수행
        for lot in self.parking_lots:
            try:
                # 각 주차장의 차량 수 시뮬레이션 업데이트
                lot.update_vehicle_count()
                updated_count += 1
                
            except Exception as e:
                # 개별 주차장 업데이트 실패 시 로깅하고 계속 진행
                # 이렇게 하면 하나의 주차장 오류가 전체를 중단시키지 않음
                self.logger.error(f"주차장 '{lot.name}' 업데이트 실패: {e}")
                
        # 업데이트 완료 통계 로깅 (성공/실패 비율 포함)
        self.logger.debug(f"'{self.name}' 주차장 상태 업데이트 완료: {updated_count}/{len(self.parking_lots)} 주차장 처리됨")

    def display_dong_status(self) -> None:
        """
        자신에게 속한 모든 주차장의 현황을 출력합니다.
        
        등록된 모든 주차장의 현재 상태를 사용자 친화적인 형태로 출력합니다.
        등록된 주차장이 없는 경우와 개별 주차장 출력 실패 시에도 적절한 메시지를 제공합니다.
        
        이 메서드는 견고한 오류 처리와 함께 사용자에게 명확한 정보를 제공합니다.
        
        Returns:
            None
            
        Output Format:
            --- 동이름 주차장 현황 ---
            총 X개 주차장이 등록되어 있습니다.
            - 주차장명 (위치): 현재차량수 / 총공간수 (점유율%)
            
        Example:
            >>> dong = Dong("강남동")
            >>> dong.display_dong_status()
            --- 강남동 주차장 현황 ---
            총 2개 주차장이 등록되어 있습니다.
            - 강남주차장 (강남역): 45 / 100 (45.0%)
            - 서초주차장 (서초역): 30 / 80 (37.5%)
        """
        # 동 현황 헤더 출력
        print(f"\n--- {self.name} 주차장 현황 ---")
        
        # 등록된 주차장이 없는 경우 처리
        if not self.parking_lots:
            print("  등록된 주차장이 없습니다.")
            self.logger.info(f"'{self.name}' 현황 출력: 등록된 주차장 없음")
        else:
            # 주차장 개수 정보 출력
            total_lots = len(self.parking_lots)
            print(f"  총 {total_lots}개 주차장이 등록되어 있습니다.")
            
            # 각 주차장의 현황을 순차적으로 출력
            for lot in self.parking_lots:
                try:
                    # 각 주차장의 상태 출력 (점유율 포함)
                    lot.display_status()
                    
                except Exception as e:
                    # 개별 주차장 출력 실패 시 오류 메시지 표시
                    # 이렇게 하면 하나의 주차장 오류가 전체 출력을 중단시키지 않음
                    self.logger.error(f"주차장 '{lot.name}' 현황 출력 실패: {e}")
                    print(f"  - {lot.name}: 현황 출력 오류")
                    
            # 출력 완료 통계 로깅
            self.logger.info(f"'{self.name}' 현황 출력 완료: {total_lots}개 주차장 처리됨")
    
    def get_total_lots(self) -> int:
        """
        등록된 주차장의 총 개수를 반환합니다.
        
        현재 관리하고 있는 주차장의 총 개수를 반환합니다.
        이는 통계 정보나 시스템 상태 확인에 유용하며, O(1) 시간복잡도로 처리됩니다.
        
        Returns:
            int: 등록된 주차장의 개수 (0 이상의 정수)
                - 0: 주차장이 등록되지 않은 상태
                - 양수: 등록된 주차장의 개수
                
        Example:
            >>> dong = Dong("강남동")
            >>> lot1 = ParkingLot("주차장1", 50, "위치1")
            >>> lot2 = ParkingLot("주차장2", 30, "위치2")
            >>> dong.add_lot(lot1)
            >>> dong.add_lot(lot2)
            >>> count = dong.get_total_lots()
            >>> print(count)  # 2
            
        Note:
            이 메서드는 단순히 리스트의 길이를 반환하므로 매우 빠릅니다.
            주차장이 추가되거나 제거될 때마다 자동으로 업데이트됩니다.
        """
        # 리스트의 길이를 반환 (O(1) 시간복잡도)
        return len(self.parking_lots)
    
    def get_lot_names(self) -> list[str]:
        """
        등록된 모든 주차장의 이름 목록을 반환합니다.
        
        현재 관리하고 있는 모든 주차장의 이름을 리스트 형태로 반환합니다.
        이는 주차장 목록을 순회하거나 사용자에게 선택지를 제공할 때 유용합니다.
        
        Returns:
            list[str]: 주차장 이름 목록 (빈 리스트일 수 있음)
                - 빈 리스트: 주차장이 등록되지 않은 경우
                - 문자열 리스트: 등록된 주차장들의 이름 목록
                
        Example:
            >>> dong = Dong("강남동")
            >>> lot1 = ParkingLot("강남주차장", 100, "강남역")
            >>> lot2 = ParkingLot("서초주차장", 80, "서초역")
            >>> dong.add_lot(lot1)
            >>> dong.add_lot(lot2)
            >>> names = dong.get_lot_names()
            >>> print(names)  # ['강남주차장', '서초주차장']
            
        Note:
            - 리스트 컴프리헨션을 사용하여 효율적으로 이름 목록을 생성합니다
            - 주차장이 추가되거나 제거될 때마다 자동으로 업데이트됩니다
            - 반환된 리스트는 복사본이므로 수정해도 원본에 영향을 주지 않습니다
        """
        # 리스트 컴프리헨션을 사용하여 주차장 이름 목록 생성
        return [lot.name for lot in self.parking_lots]
    
    def remove_lot(self, lot_name: str) -> bool:
        """
        등록된 주차장을 제거합니다.
        
        지정된 이름의 주차장을 관리 목록에서 제거합니다.
        주차장이 존재하지 않거나 잘못된 입력값인 경우 실패를 반환합니다.
        
        이 메서드는 안전한 주차장 제거를 보장하며, 모든 작업 과정을 로깅합니다.
        
        Args:
            lot_name: 제거할 주차장의 이름
                - 문자열 타입이어야 함
                - None이나 빈 문자열은 허용되지 않음
                
        Returns:
            bool: 제거 성공 시 True, 실패 시 False
                - True: 주차장이 성공적으로 제거됨
                - False: 유효성 검사 실패, 주차장 미존재, 또는 예외 발생
                
        Warning:
            주차장을 제거하면 해당 주차장의 모든 정보도 함께 삭제됩니다.
            이 작업은 되돌릴 수 없으므로 신중하게 사용해야 합니다.
            
        Example:
            >>> dong = Dong("강남동")
            >>> lot = ParkingLot("강남주차장", 100, "강남역")
            >>> dong.add_lot(lot)
            >>> success = dong.remove_lot("강남주차장")
            >>> print(success)  # True
            
        Note:
            - 제거 작업은 O(n) 시간복잡도를 가집니다 (n은 주차장 개수)
            - 제거 성공 시 로그에 기록됩니다
            - 존재하지 않는 주차장 제거 시도는 경고 로그를 남깁니다
        """
        # 입력값 유효성 검사: None, 빈 문자열, 잘못된 타입 체크
        if not lot_name or not isinstance(lot_name, str):
            self.logger.error(f"잘못된 주차장 이름: {lot_name}")
            return False
            
        # 주차장 찾기 및 제거 (O(n) 시간복잡도)
        for i, lot in enumerate(self.parking_lots):
            if lot.name == lot_name:
                # 주차장을 리스트에서 제거하고 로깅
                removed_lot = self.parking_lots.pop(i)
                self.logger.info(f"주차장 '{removed_lot.name}' 제거됨")
                return True
                
        # 주차장을 찾지 못한 경우 경고 로깅
        self.logger.warning(f"제거할 주차장 '{lot_name}'이 존재하지 않음")
        return False
    
    def get_lot_by_name(self, lot_name: str) -> Optional['ParkingLot']:
        """
        이름으로 특정 주차장 객체를 찾아 반환합니다.
        
        지정된 이름의 주차장을 검색하여 반환합니다.
        존재하지 않는 경우 None을 반환합니다.
        
        이 메서드는 주차장 객체에 직접 접근할 때 사용되며,
        검색 과정에서 발생하는 모든 작업을 로깅합니다.
        
        Args:
            lot_name: 찾을 주차장의 이름
                - 문자열 타입이어야 함
                - None이나 빈 문자열은 허용되지 않음
                
        Returns:
            Optional[ParkingLot]: 찾은 주차장 객체 또는 None
                - ParkingLot 객체: 주차장을 찾은 경우
                - None: 주차장을 찾지 못한 경우 또는 입력값 오류
                
        Example:
            >>> dong = Dong("강남동")
            >>> lot = ParkingLot("강남주차장", 100, "강남역")
            >>> dong.add_lot(lot)
            >>> found_lot = dong.get_lot_by_name("강남주차장")
            >>> print(found_lot.name)  # "강남주차장"
            
        Note:
            - 검색 작업은 O(n) 시간복잡도를 가집니다 (n은 주차장 개수)
            - 검색 성공 시 debug 레벨 로그를 남깁니다
            - 검색 실패 시 warning 레벨 로그를 남깁니다
        """
        # 입력값 유효성 검사: None, 빈 문자열, 잘못된 타입 체크
        if not lot_name or not isinstance(lot_name, str):
            self.logger.error(f"잘못된 주차장 이름: {lot_name}")
            return None
            
        # 주차장 검색 (O(n) 시간복잡도)
        for lot in self.parking_lots:
            if lot.name == lot_name:
                # 검색 성공 시 로깅 및 객체 반환
                self.logger.debug(f"주차장 '{lot_name}' 검색 성공")
                return lot
                
        # 주차장을 찾지 못한 경우 경고 로깅
        self.logger.warning(f"주차장 '{lot_name}'을 찾을 수 없음")
        return None
    
    def get_occupancy_summary(self) -> dict:
        """
        동 전체의 주차장 점유율 요약 정보를 반환합니다.
        
        등록된 모든 주차장의 점유율을 분석하여 통계 정보를 제공합니다.
        이 메서드는 동 전체의 주차장 운영 현황을 한눈에 파악할 수 있게 해줍니다.
        
        Returns:
            dict: 점유율 요약 정보를 담은 딕셔너리
                - total_spaces (int): 전체 주차 공간 수
                - total_cars (int): 전체 주차된 차량 수
                - overall_occupancy_rate (float): 전체 점유율 (0.0 ~ 1.0)
                - lot_count (int): 주차장 개수
                
        Example:
            >>> dong = Dong("강남동")
            >>> lot1 = ParkingLot("주차장1", 100, "위치1")
            >>> lot2 = ParkingLot("주차장2", 50, "위치2")
            >>> dong.add_lot(lot1)
            >>> dong.add_lot(lot2)
            >>> summary = dong.get_occupancy_summary()
            >>> print(summary['overall_occupancy_rate'])  # 0.45 (45%)
            >>> print(summary['total_spaces'])  # 150
            
        Note:
            - 주차장이 없는 경우 모든 값이 0인 딕셔너리를 반환합니다
            - 점유율은 전체 주차된 차량 수를 전체 주차 공간 수로 나눈 값입니다
            - 계산 결과는 로그에 기록됩니다
        """
        # 주차장이 없는 경우 빈 요약 정보 반환
        if not self.parking_lots:
            return {
                'total_spaces': 0,
                'total_cars': 0,
                'overall_occupancy_rate': 0.0,
                'lot_count': 0
            }
            
        # 전체 주차 공간 수 계산 (모든 주차장의 총 공간 합계)
        total_spaces = sum(lot.total_spaces for lot in self.parking_lots)
        
        # 전체 주차된 차량 수 계산 (모든 주차장의 현재 차량 수 합계)
        total_cars = sum(lot.current_cars for lot in self.parking_lots)
        
        # 전체 점유율 계산 (0으로 나누기 방지)
        overall_occupancy_rate = total_cars / total_spaces if total_spaces > 0 else 0.0
        
        # 요약 정보 딕셔너리 생성
        summary = {
            'total_spaces': total_spaces,
            'total_cars': total_cars,
            'overall_occupancy_rate': overall_occupancy_rate,
            'lot_count': len(self.parking_lots)
        }
        
        # 점유율 요약 정보 로깅 (퍼센트 형태로 표시)
        self.logger.info(f"'{self.name}' 점유율 요약: {overall_occupancy_rate:.2%}")
        return summary

class ParkingLot:
    """
    개별 주차장 하나의 정보와 기능을 담당하는 클래스.
    가장 기본적인 데이터 단위입니다.
    
    이 클래스는 단일 주차장의 모든 정보와 기능을 관리하며,
    차량 수 시뮬레이션, 상태 출력, 점유율 계산 등의 기능을 제공합니다.
    
    ParkingLot 클래스는 주차장 관리 시스템의 최하위 계층으로,
    실제 주차장의 물리적 특성과 동작을 모델링합니다.
    
    Attributes:
        name (str): 주차장 이름 (예: "강남주차장", "서초주차장")
        total_spaces (int): 총 주차 공간 수 (양의 정수)
        location_info (str): 주차장 위치 정보 (예: "강남역 근처", "서초역 2번 출구")
        current_cars (int): 현재 주차된 차량 수 (0 ~ total_spaces)
        logger (logging.Logger): 로깅을 위한 로거 객체 (주차장별로 구분됨)
        
    Example:
        >>> lot = ParkingLot("강남주차장", 100, "강남역 근처")
        >>> lot.display_status()
        - 강남주차장 (강남역 근처): 45 / 100 (45.0%)
    """
    def __init__(self, name: str, total_spaces: int, location_info: str, parking_type: str = "무료", price_info: str = None) -> None:
        """
        ParkingLot 객체를 초기화합니다.
        
        주차장의 기본 정보를 설정하고, 초기 차량 수를 랜덤하게 설정합니다.
        모든 입력값의 유효성을 검사하여 데이터 무결성을 보장합니다.
        
        Args:
            name: 주차장 이름 (비어있지 않은 문자열)
                - 예: "강남주차장", "서초주차장", "마포주차장"
                - None, 빈 문자열, 또는 문자열이 아닌 타입은 허용되지 않음
            total_spaces: 총 주차 공간 수 (양의 정수)
                - 1 이상의 정수여야 함
                - 0 이하의 값은 허용되지 않음
            location_info: 주차장 위치 정보 (비어있지 않은 문자열)
                - 예: "강남역 근처", "서초역 2번 출구"
                - None, 빈 문자열, 또는 문자열이 아닌 타입은 허용되지 않음
            parking_type: 주차장 유형 (기본값: "무료")
                - "무료": 무료 주차장
                - "유료": 유료 주차장
            price_info: 가격 정보 (기본값: None)
                - None: 유형에 따라 자동 설정
                - "무료": "무료"로 설정
                - "유료": "최초 30분 무료, 그후 30분당 500원"으로 설정
                
        Raises:
            ValueError: 입력값이 유효하지 않은 경우
                - name이 None, 빈 문자열, 또는 문자열이 아닌 경우
                - total_spaces가 양의 정수가 아닌 경우
                - location_info가 None, 빈 문자열, 또는 문자열이 아닌 경우
                - parking_type이 "무료" 또는 "유료"가 아닌 경우
                
        Example:
            >>> lot = ParkingLot("강남주차장", 100, "강남역 근처", "유료")
            >>> print(lot.name)  # "강남주차장"
            >>> print(lot.total_spaces)  # 100
            >>> print(lot.parking_type)  # "유료"
            >>> print(lot.current_cars)  # 0 ~ 100 사이의 랜덤 값
        """
        # 입력값 유효성 검사: None, 빈 문자열, 잘못된 타입 체크
        if not name or not isinstance(name, str):
            raise ValueError("주차장 이름은 비어있지 않은 문자열이어야 합니다")
        if not isinstance(total_spaces, int) or total_spaces <= 0:
            raise ValueError("총 주차 공간은 양의 정수여야 합니다")
        if not location_info or not isinstance(location_info, str):
            raise ValueError("위치 정보는 비어있지 않은 문자열이어야 합니다")
        if parking_type not in ["무료", "유료"]:
            raise ValueError("주차장 유형은 '무료' 또는 '유료'여야 합니다")
            
        # 주차장 기본 정보 저장
        self.name = name
        self.total_spaces = total_spaces
        self.location_info = location_info
        self.parking_type = parking_type
        
        # 가격 정보 설정
        if price_info is not None:
            self.price_info = price_info
        elif parking_type == "유료":
            self.price_info = "최초 30분 무료, 그후 30분당 500원"
        elif parking_type == "무료":
            self.price_info = "무료"
        else:
            self.price_info = "가격 정보 없음"
        
        # 초기 주차 차량은 0대에서 총 공간 사이에서 임의로 설정
        # 실제 운영 환경에서는 센서나 데이터베이스에서 초기값을 가져올 수 있음
        self.current_cars = random.randint(MIN_CARS, total_spaces)
        
        # 주차장별 로거 생성 (로그에서 주차장을 구분할 수 있도록)
        self.logger = logging.getLogger(f"{__name__}.{name}")

    def update_vehicle_count(self) -> dict:
        """
        차량이 들어오거나 나가는 상황을 시뮬레이션하여 주차된 차량 수를 변경합니다.
        
        랜덤 확률을 기반으로 차량의 진입과 출차를 시뮬레이션합니다.
        주차장이 가득 찬 경우 진입을 제한하고, 빈 경우 출차를 제한합니다.
        
        이 메서드는 실제 주차장의 동적 특성을 모델링하며, 견고한 오류 처리를 제공합니다.
        
        Returns:
            dict: 차량 수 변화 정보를 담은 딕셔너리
                - old_count (int): 변경 전 차량 수
                - new_count (int): 변경 후 차량 수
                - change (int): 변화량 (양수: 진입, 음수: 출차, 0: 변화 없음)
                - action (str): 수행된 동작 ("진입", "출차", "변화없음", "오류")
                
        Example:
            >>> lot = ParkingLot("강남주차장", 100, "강남역")
            >>> result = lot.update_vehicle_count()
            >>> print(result['action'])  # "진입" 또는 "출차" 또는 "변화없음"
            >>> print(result['change'])  # 1 (진입), -1 (출차), 0 (변화없음)
            
        Note:
            - 진입 확률은 DEFAULT_ENTRY_PROBABILITY 상수로 제어됩니다
            - 주차장이 가득 찬 경우 진입이 제한됩니다
            - 주차장이 비어있는 경우 출차가 제한됩니다
            - 모든 작업 과정이 로그에 기록됩니다
        """
        # 변경 전 차량 수 저장 (결과 반환용)
        old_count = self.current_cars
        
        try:
            # 랜덤한 차량 수량 생성 (1 ~ MAX_VEHICLE_CHANGE 사이)
            random_change_amount = random.randint(1, MAX_VEHICLE_CHANGE)
            
            # 진입과 출차 확률을 각각 계산
            entry_roll = random.random()
            exit_roll = random.random()
            
            # 진입 조건: 진입 확률을 통과하고, 주차장에 공간이 있는 경우
            if (entry_roll > DEFAULT_ENTRY_PROBABILITY and 
                self.current_cars < self.total_spaces):
                
                # 진입 가능한 최대 수량 계산 (가득 찰 때까지)
                max_entry = min(random_change_amount, self.total_spaces - self.current_cars)
                self.current_cars += max_entry
                action = "진입"
                self.logger.debug(f"차량 {max_entry}대 진입: {old_count} -> {self.current_cars}")
                
            # 출차 조건: 출차 확률을 통과하고, 주차장에 차량이 있는 경우
            elif (exit_roll > DEFAULT_EXIT_PROBABILITY and 
                  self.current_cars > MIN_CARS):
                
                # 출차 가능한 최대 수량 계산 (비워질 때까지)
                max_exit = min(random_change_amount, self.current_cars)
                self.current_cars -= max_exit
                action = "출차"
                self.logger.debug(f"차량 {max_exit}대 출차: {old_count} -> {self.current_cars}")
                
            else:
                # 변화 없음: 진입/출차 조건을 만족하지 않는 경우
                action = "변화없음"
                self.logger.debug(f"차량 수 변화 없음: {self.current_cars}")
                
            # 변화량 계산 (양수: 진입, 음수: 출차, 0: 변화 없음)
            change = self.current_cars - old_count
            
            # 결과 딕셔너리 생성 (호출자가 변화 정보를 확인할 수 있도록)
            result = {
                'old_count': old_count,
                'new_count': self.current_cars,
                'change': change,
                'action': action
            }
            
            return result
            
        except Exception as e:
            # 예외 발생 시 오류 로깅 및 기본값 반환
            # 이렇게 하면 예외가 발생해도 시스템이 중단되지 않음
            self.logger.error(f"차량 수 업데이트 실패: {e}")
            return {
                'old_count': old_count,
                'new_count': self.current_cars,
                'change': 0,
                'action': "오류"
            }

    def display_status(self) -> None:
        """
        해당 주차장의 현재 상태를 정해진 형식으로 출력합니다.
        
        주차장의 현재 상태를 사용자 친화적인 형태로 출력합니다.
        점유율 정보와 주차장 유형을 포함하여 더 유용한 정보를 제공합니다.
        
        이 메서드는 견고한 오류 처리와 함께 사용자에게 명확한 정보를 제공합니다.
        
        Returns:
            None
            
        Output Format:
            - 주차장명 (위치) [유형]: 현재차량수 / 총공간수 (점유율%)
            
        Example:
            >>> lot = ParkingLot("강남주차장", 100, "강남역", "유료")
            >>> lot.current_cars = 45
            >>> lot.display_status()
            - 강남주차장 (강남역) [유료]: 45 / 100 (45.0%)
            
        Note:
            - 점유율은 소수점 첫째 자리까지 표시됩니다
            - 주차장 유형이 대괄호 안에 표시됩니다
            - 0으로 나누기 오류를 방지하기 위해 안전한 계산을 수행합니다
            - 출력 실패 시에도 기본 메시지를 표시합니다
        """
        try:
            # 점유율 계산 (0으로 나누기 방지)
            # total_spaces가 0인 경우를 대비한 안전한 계산
            occupancy_rate = (self.current_cars / self.total_spaces) * 100 if self.total_spaces > 0 else 0.0
            
            # 상태 정보 출력 (점유율 및 주차장 유형 포함)
            # 사용자에게 직관적인 정보 제공 (현재/총 공간, 점유율, 유형)
            print(f"  - {self.name} ({self.location_info}) [{self.parking_type}]: {self.current_cars} / {self.total_spaces} ({occupancy_rate:.1f}%)")
            
            # 출력 완료 로깅 (디버그 레벨)
            self.logger.debug(f"상태 출력 완료: {self.current_cars}/{self.total_spaces} ({occupancy_rate:.1f}%) [{self.parking_type}]")
            
        except Exception as e:
            # 출력 실패 시 오류 로깅 및 기본 메시지 출력
            # 이렇게 하면 출력 오류가 발생해도 사용자에게 정보를 제공할 수 있음
            self.logger.error(f"상태 출력 실패: {e}")
            print(f"  - {self.name} ({self.location_info}) [{self.parking_type}]: 출력 오류")
    
    def get_occupancy_rate(self) -> float:
        """
        주차장의 현재 점유율을 반환합니다.
        
        현재 주차된 차량 수를 총 주차 공간 수로 나눈 점유율을 계산합니다.
        이 메서드는 주차장의 이용률을 분석하는 데 유용합니다.
        
        Returns:
            float: 점유율 (0.0 ~ 1.0)
                - 0.0: 주차장이 비어있음 (0%)
                - 1.0: 주차장이 가득 참 (100%)
                - 0.0 ~ 1.0: 부분 점유 상태 (0% ~ 100%)
                
        Example:
            >>> lot = ParkingLot("강남주차장", 100, "강남역")
            >>> lot.current_cars = 45
            >>> rate = lot.get_occupancy_rate()
            >>> print(rate)  # 0.45
            >>> print(f"{rate:.1%}")  # 45.0%
            
        Note:
            - 총 주차 공간이 0인 경우 0.0을 반환합니다
            - 계산 결과는 로그에 기록됩니다
        """
        # 총 주차 공간이 0인 경우 예외 처리
        if self.total_spaces <= 0:
            self.logger.warning("총 주차 공간이 0이므로 점유율을 계산할 수 없습니다")
            return 0.0
            
        # 점유율 계산 (현재 차량 수 / 총 공간 수)
        occupancy_rate = self.current_cars / self.total_spaces
        self.logger.debug(f"점유율 계산: {occupancy_rate:.2%}")
        return occupancy_rate
    
    def is_full(self) -> bool:
        """
        주차장이 가득 찼는지 확인합니다.
        
        현재 주차된 차량 수가 총 주차 공간 수와 같거나 큰지 확인합니다.
        이 메서드는 새로운 차량의 진입 가능 여부를 판단하는 데 사용됩니다.
        
        Returns:
            bool: 주차장이 가득 찬 경우 True, 그렇지 않으면 False
                - True: current_cars >= total_spaces
                - False: current_cars < total_spaces
                
        Example:
            >>> lot = ParkingLot("강남주차장", 100, "강남역")
            >>> lot.current_cars = 100
            >>> print(lot.is_full())  # True
            >>> lot.current_cars = 99
            >>> print(lot.is_full())  # False
            
        Note:
            - 가득 찬 상태일 때 로그에 기록됩니다
            - 이 메서드는 O(1) 시간복잡도를 가집니다
        """
        # 가득 찬 상태 확인 (현재 차량 수 >= 총 공간 수)
        is_full_status = self.current_cars >= self.total_spaces
        if is_full_status:
            self.logger.debug("주차장이 가득 참")
        return is_full_status
    
    def is_empty(self) -> bool:
        """
        주차장이 비어있는지 확인합니다.
        
        현재 주차된 차량 수가 최소값(MIN_CARS) 이하인지 확인합니다.
        이 메서드는 주차장의 이용 가능 여부를 판단하는 데 사용됩니다.
        
        Returns:
            bool: 주차장이 비어있는 경우 True, 그렇지 않으면 False
                - True: current_cars <= MIN_CARS (0)
                - False: current_cars > MIN_CARS
                
        Example:
            >>> lot = ParkingLot("강남주차장", 100, "강남역")
            >>> lot.current_cars = 0
            >>> print(lot.is_empty())  # True
            >>> lot.current_cars = 1
            >>> print(lot.is_empty())  # False
            
        Note:
            - 비어있는 상태일 때 로그에 기록됩니다
            - 이 메서드는 O(1) 시간복잡도를 가집니다
        """
        # 비어있는 상태 확인 (현재 차량 수 <= 최소값)
        is_empty_status = self.current_cars <= MIN_CARS
        if is_empty_status:
            self.logger.debug("주차장이 비어있음")
        return is_empty_status
    
    def get_available_spaces(self) -> int:
        """
        사용 가능한 주차 공간 수를 반환합니다.
        
        총 주차 공간 수에서 현재 주차된 차량 수를 뺀 값을 계산합니다.
        이 메서드는 새로운 차량이 주차할 수 있는 공간 수를 확인하는 데 사용됩니다.
        
        Returns:
            int: 사용 가능한 주차 공간 수 (0 이상)
                - 0: 주차장이 가득 참 (사용 가능한 공간 없음)
                - 양수: 사용 가능한 공간 수 (total_spaces - current_cars)
                
        Example:
            >>> lot = ParkingLot("강남주차장", 100, "강남역")
            >>> lot.current_cars = 45
            >>> available = lot.get_available_spaces()
            >>> print(available)  # 55
            
        Note:
            - max(0, ...)를 사용하여 음수 값 방지
            - 계산 결과는 로그에 기록됩니다
        """
        # 사용 가능한 공간 계산 (총 공간 - 현재 차량 수)
        # max(0, ...)를 사용하여 음수 값 방지
        available_spaces = max(0, self.total_spaces - self.current_cars)
        self.logger.debug(f"사용 가능한 공간: {available_spaces}개")
        return available_spaces
    
    def get_status_summary(self) -> dict:
        """
        주차장의 현재 상태 요약 정보를 반환합니다.
        
        주차장의 모든 주요 상태 정보를 하나의 딕셔너리로 통합하여 반환합니다.
        이 메서드는 주차장의 전체적인 상황을 한눈에 파악하는 데 유용합니다.
        
        Returns:
            dict: 주차장 상태 요약 정보를 담은 딕셔너리
                - name (str): 주차장 이름
                - location (str): 위치 정보
                - current_cars (int): 현재 주차된 차량 수
                - total_spaces (int): 총 주차 공간 수
                - available_spaces (int): 사용 가능한 공간 수
                - occupancy_rate (float): 점유율 (0.0 ~ 1.0)
                - is_full (bool): 가득 찬 여부
                - is_empty (bool): 비어있는 여부
                
        Example:
            >>> lot = ParkingLot("강남주차장", 100, "강남역")
            >>> lot.current_cars = 45
            >>> summary = lot.get_status_summary()
            >>> print(summary['occupancy_rate'])  # 0.45
            >>> print(summary['available_spaces'])  # 55
            >>> print(summary['is_full'])  # False
            
        Note:
            - 모든 상태 정보가 한 번에 계산되어 반환됩니다
            - 요약 생성 시 로그에 기록됩니다
        """
        # 점유율 계산 (다른 메서드들을 호출하여 계산)
        occupancy_rate = self.get_occupancy_rate()
        
        # 상태 요약 딕셔너리 생성
        summary = {
            'name': self.name,
            'location': self.location_info,
            'current_cars': self.current_cars,
            'total_spaces': self.total_spaces,
            'available_spaces': self.get_available_spaces(),
            'occupancy_rate': occupancy_rate,
            'is_full': self.is_full(),
            'is_empty': self.is_empty()
        }
        
        # 요약 생성 완료 로깅
        self.logger.info(f"상태 요약 생성: {occupancy_rate:.2%} 점유")
        return summary
    
    def set_vehicle_count(self, count: int) -> bool:
        """
        주차된 차량 수를 직접 설정합니다.
        
        시뮬레이션이 아닌 직접적인 방법으로 주차된 차량 수를 설정합니다.
        이 메서드는 테스트, 초기화, 또는 수동 조정 시에 사용됩니다.
        
        Args:
            count: 설정할 차량 수 (0 이상, total_spaces 이하)
                - 정수 타입이어야 함
                - 0 이상의 값이어야 함
                - total_spaces 이하의 값이어야 함
                
        Returns:
            bool: 설정 성공 시 True, 실패 시 False
                - True: 차량 수가 성공적으로 설정됨
                - False: 입력값이 유효하지 않음
                
        Example:
            >>> lot = ParkingLot("강남주차장", 100, "강남역")
            >>> success = lot.set_vehicle_count(50)
            >>> print(success)  # True
            >>> print(lot.current_cars)  # 50
            
            >>> # 잘못된 값 설정 시도
            >>> success = lot.set_vehicle_count(150)
            >>> print(success)  # False (100을 초과)
            
        Note:
            - 설정 전후의 값이 로그에 기록됩니다
            - 유효하지 않은 값은 거부되고 False를 반환합니다
            - 이 메서드는 시뮬레이션과 별개로 동작합니다
        """
        # 입력값 유효성 검사: 타입, 범위 체크
        if not isinstance(count, int) or count < 0 or count > self.total_spaces:
            self.logger.error(f"잘못된 차량 수: {count} (0 ~ {self.total_spaces} 범위여야 함)")
            return False
            
        # 변경 전 차량 수 저장 (로깅용)
        old_count = self.current_cars
        
        # 차량 수 설정
        self.current_cars = count
        
        # 설정 완료 로깅 (변경 전후 값 포함)
        self.logger.info(f"차량 수 변경: {old_count} -> {count}")
        return True
    
    def simulate_parking_changes(self) -> None:
        """
        주차장 상태를 랜덤하게 시뮬레이션합니다.
        
        실제 운영 환경에서는 센서나 데이터베이스에서 실시간 데이터를 가져오지만,
        시뮬레이션을 위해 랜덤하게 차량 수를 변경합니다.
        """
        import random
        
        # 현재 차량 수에서 ±5 범위로 랜덤하게 변경
        change = random.randint(-5, 5)
        new_count = self.current_cars + change
        
        # 범위 제한 (0 ~ total_spaces)
        new_count = max(0, min(new_count, self.total_spaces))
        
        # 변경이 있을 때만 업데이트
        if new_count != self.current_cars:
            old_count = self.current_cars
            self.current_cars = new_count
            self.logger.info(f"주차장 '{self.name}' 시뮬레이션: {old_count} -> {new_count}")
