# user_auth.py
"""
사용자 인증 및 개인화 시스템
- 회원가입/로그인
- 계정별 즐겨찾기 영구 저장
- 추가/삭제 완벽 지원
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

class UserAuthSystem:
    """사용자 인증 및 개인 데이터 관리 시스템"""
    
    def __init__(self, data_file: str = "users_data.json"):
        """
        사용자 인증 시스템 초기화
        
        Args:
            data_file: 사용자 데이터를 저장할 JSON 파일 경로
        """
        self.data_file = data_file
        self.users: Dict = {}
        self.load_data()
    
    def load_data(self) -> None:
        """저장된 사용자 데이터 로드 (영구 저장된 데이터)"""
        if Path(self.data_file).exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
                logger.info(f"사용자 데이터 로드 완료: {len(self.users)}명")
            except Exception as e:
                logger.error(f"데이터 로드 실패: {e}")
                self.users = {}
        else:
            self.users = {}
            logger.info("새 사용자 데이터 파일 생성 예정")
    
    def save_data(self) -> bool:
        """사용자 데이터 영구 저장"""
        try:
            # 백업 생성
            if Path(self.data_file).exists():
                backup_file = f"{self.data_file}.backup"
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    backup_data = f.read()
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(backup_data)
            
            # 데이터 저장
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
            
            logger.info("사용자 데이터 저장 완료")
            return True
        except Exception as e:
            logger.error(f"데이터 저장 실패: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """비밀번호 암호화 (SHA256)"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    # ==================== 회원가입/로그인 ====================
    
    def register(self, username: str, password: str, email: str = "") -> Tuple[bool, str]:
        """
        회원가입 (영구 저장)
        
        Args:
            username: 사용자 아이디
            password: 비밀번호
            email: 이메일 (선택)
            
        Returns:
            (성공여부, 메시지)
        """
        # 유효성 검사
        if not username or len(username) < 3:
            return False, "아이디는 3자 이상이어야 합니다."
        
        if not password or len(password) < 4:
            return False, "비밀번호는 4자 이상이어야 합니다."
        
        # 중복 체크
        if username in self.users:
            return False, "이미 존재하는 아이디입니다."
        
        # 사용자 생성
        self.users[username] = {
            "password": self.hash_password(password),
            "email": email,
            "favorites": [],  # 즐겨찾기 목록 (영구 저장)
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
        
        # 파일에 저장 (영구 저장)
        if self.save_data():
            logger.info(f"새 사용자 등록: {username}")
            return True, f"회원가입 완료! {username}님 환영합니다!"
        else:
            del self.users[username]  # 저장 실패 시 롤백
            return False, "데이터 저장 중 오류가 발생했습니다."
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        로그인
        
        Args:
            username: 사용자 아이디
            password: 비밀번호
            
        Returns:
            (성공여부, 메시지)
        """
        if username not in self.users:
            return False, "존재하지 않는 아이디입니다."
        
        if self.users[username]["password"] != self.hash_password(password):
            return False, "비밀번호가 일치하지 않습니다."
        
        # 마지막 로그인 시간 업데이트
        self.users[username]["last_login"] = datetime.now().isoformat()
        self.save_data()
        
        logger.info(f"로그인 성공: {username}")
        return True, f"환영합니다, {username}님!"
    
    def change_password(self, username: str, current_password: str, new_password: str) -> Tuple[bool, str]:
        """
        비밀번호 변경
        
        Args:
            username: 사용자 아이디
            current_password: 현재 비밀번호
            new_password: 새 비밀번호
            
        Returns:
            (성공여부, 메시지)
        """
        # 현재 비밀번호 확인
        success, _ = self.login(username, current_password)
        if not success:
            return False, "현재 비밀번호가 일치하지 않습니다."
        
        # 새 비밀번호 유효성 검사
        if len(new_password) < 4:
            return False, "새 비밀번호는 4자 이상이어야 합니다."
        
        # 비밀번호 변경
        self.users[username]["password"] = self.hash_password(new_password)
        
        if self.save_data():
            logger.info(f"비밀번호 변경: {username}")
            return True, "비밀번호가 변경되었습니다."
        else:
            return False, "비밀번호 변경 중 오류가 발생했습니다."
    
    def delete_account(self, username: str, password: str) -> Tuple[bool, str]:
        """
        계정 삭제 (영구 삭제)
        
        Args:
            username: 사용자 아이디
            password: 비밀번호 확인
            
        Returns:
            (성공여부, 메시지)
        """
        # 비밀번호 확인
        success, _ = self.login(username, password)
        if not success:
            return False, "비밀번호가 일치하지 않습니다."
        
        # 계정 삭제
        if username in self.users:
            del self.users[username]
            if self.save_data():
                logger.info(f"계정 삭제: {username}")
                return True, "계정이 삭제되었습니다."
            else:
                return False, "계정 삭제 중 오류가 발생했습니다."
        
        return False, "계정을 찾을 수 없습니다."
    
    # ==================== 즐겨찾기 관리 (영구 저장) ====================
    
    def add_favorite(self, username: str, dong_name: str, lot_name: str) -> Tuple[bool, str]:
        """
        즐겨찾기 추가 (영구 저장)
        
        Args:
            username: 사용자 아이디
            dong_name: 동 이름
            lot_name: 주차장 이름
            
        Returns:
            (성공여부, 메시지)
        """
        if username not in self.users:
            return False, "로그인이 필요합니다."
        
        # 즐겨찾기 데이터 구조
        favorite = {
            "dong_name": dong_name,
            "lot_name": lot_name,
            "added_at": datetime.now().isoformat()
        }
        
        # 중복 체크
        existing_favorites = self.users[username]["favorites"]
        for fav in existing_favorites:
            if fav["dong_name"] == dong_name and fav["lot_name"] == lot_name:
                return False, "이미 즐겨찾기에 있습니다."
        
        # 추가
        self.users[username]["favorites"].append(favorite)
        
        # 파일에 저장 (영구 저장)
        if self.save_data():
            logger.info(f"즐겨찾기 추가: {username} - {dong_name}:{lot_name}")
            return True, f"{lot_name}이(가) 즐겨찾기에 추가되었습니다!"
        else:
            # 저장 실패 시 롤백
            self.users[username]["favorites"].pop()
            return False, "저장 중 오류가 발생했습니다."
    
    def remove_favorite(self, username: str, dong_name: str, lot_name: str) -> Tuple[bool, str]:
        """
        즐겨찾기 삭제 (영구 삭제)
        
        Args:
            username: 사용자 아이디
            dong_name: 동 이름
            lot_name: 주차장 이름
            
        Returns:
            (성공여부, 메시지)
        """
        if username not in self.users:
            return False, "로그인이 필요합니다."
        
        # 삭제
        favorites = self.users[username]["favorites"]
        for i, fav in enumerate(favorites):
            if fav["dong_name"] == dong_name and fav["lot_name"] == lot_name:
                removed = favorites.pop(i)
                
                # 파일에 저장 (영구 저장)
                if self.save_data():
                    logger.info(f"즐겨찾기 삭제: {username} - {dong_name}:{lot_name}")
                    return True, f"{lot_name}이(가) 즐겨찾기에서 삭제되었습니다."
                else:
                    # 실패 시 복구
                    favorites.insert(i, removed)
                    return False, "삭제 중 오류가 발생했습니다."
        
        return False, "즐겨찾기에서 찾을 수 없습니다."
    
    def clear_favorites(self, username: str) -> Tuple[bool, str]:
        """
        즐겨찾기 전체 삭제
        
        Args:
            username: 사용자 아이디
            
        Returns:
            (성공여부, 메시지)
        """
        if username not in self.users:
            return False, "로그인이 필요합니다."
        
        count = len(self.users[username]["favorites"])
        backup = self.users[username]["favorites"].copy()
        self.users[username]["favorites"] = []
        
        if self.save_data():
            logger.info(f"즐겨찾기 전체 삭제: {username} - {count}개")
            return True, f"즐겨찾기 {count}개가 모두 삭제되었습니다."
        else:
            # 실패 시 복구
            self.users[username]["favorites"] = backup
            return False, "삭제 중 오류가 발생했습니다."
    
    def get_favorites(self, username: str) -> List[Dict]:
        """
        사용자의 즐겨찾기 목록 조회
        
        Args:
            username: 사용자 아이디
            
        Returns:
            즐겨찾기 목록 (리스트)
        """
        if username not in self.users:
            return []
        
        return self.users[username]["favorites"]
    
    def get_favorites_count(self, username: str) -> int:
        """
        즐겨찾기 개수 조회
        
        Args:
            username: 사용자 아이디
            
        Returns:
            즐겨찾기 개수
        """
        return len(self.get_favorites(username))
    
    def is_favorite(self, username: str, dong_name: str, lot_name: str) -> bool:
        """
        특정 주차장이 즐겨찾기에 있는지 확인
        
        Args:
            username: 사용자 아이디
            dong_name: 동 이름
            lot_name: 주차장 이름
            
        Returns:
            즐겨찾기 여부
        """
        favorites = self.get_favorites(username)
        for fav in favorites:
            if fav["dong_name"] == dong_name and fav["lot_name"] == lot_name:
                return True
        return False
    
    # ==================== 사용자 정보 ====================
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """
        사용자 정보 조회 (비밀번호 제외)
        
        Args:
            username: 사용자 아이디
            
        Returns:
            사용자 정보 딕셔너리 또는 None
        """
        if username in self.users:
            user_data = self.users[username].copy()
            user_data.pop("password")  # 비밀번호는 제외
            return user_data
        return None
    
    def get_total_users(self) -> int:
        """
        총 사용자 수 조회
        
        Returns:
            사용자 수
        """
        return len(self.users)
    
    def start_parking(self, username: str, dong_name: str, lot_name: str, price_info: str) -> Tuple[bool, str]:
        """
        주차 시작 (입차 기록)
        
        Args:
            username: 사용자명
            dong_name: 동 이름
            lot_name: 주차장 이름
            price_info: 가격 정보
            
        Returns:
            Tuple[bool, str]: (성공 여부, 메시지)
        """
        if username not in self.users:
            return False, "사용자를 찾을 수 없습니다."
        
        # 이미 주차 중인지 확인
        if self.users[username].get('parking_record'):
            return False, "이미 주차 중입니다. 먼저 출차하세요."
        
        # 입차 기록 저장
        from datetime import datetime
        self.users[username]['parking_record'] = {
            'dong_name': dong_name,
            'lot_name': lot_name,
            'entry_time': datetime.now().isoformat(),
            'price_info': price_info
        }
        
        # 데이터 저장
        if self.save_data():
            logger.info(f"사용자 '{username}' 입차 기록 저장: {dong_name} - {lot_name}")
            return True, f"입차가 기록되었습니다. ({dong_name} - {lot_name})"
        else:
            return False, "데이터 저장에 실패했습니다."
    
    def get_current_parking(self, username: str) -> Optional[Dict]:
        """
        현재 주차 정보 조회
        
        Args:
            username: 사용자명
            
        Returns:
            Optional[Dict]: 주차 정보 (없으면 None)
        """
        if username not in self.users:
            return None
        
        return self.users[username].get('parking_record')
    
    def end_parking(self, username: str) -> Tuple[bool, str]:
        """
        주차 종료 (출차 처리)
        
        Args:
            username: 사용자명
            
        Returns:
            Tuple[bool, str]: (성공 여부, 메시지)
        """
        if username not in self.users:
            return False, "사용자를 찾을 수 없습니다."
        
        if not self.users[username].get('parking_record'):
            return False, "주차 기록이 없습니다."
        
        # 주차 기록 삭제
        del self.users[username]['parking_record']
        
        # 데이터 저장
        if self.save_data():
            logger.info(f"사용자 '{username}' 출차 처리 완료")
            return True, "출차가 완료되었습니다."
        else:
            return False, "데이터 저장에 실패했습니다."

