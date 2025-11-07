# parking_fee_calculator.py
"""
MCP Sequential Thinking을 활용한 주차 요금 계산 시스템
- 입차 시간부터 출차 시간까지의 경과 시간 계산
- 최초 30분 무료, 그후 30분당 500원 요금 체계
- 단계별 사고 과정을 통한 정확한 요금 계산
"""

from datetime import datetime
from typing import Tuple, Dict, Any
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

def calculate_fee_with_thinking(entry_time: str, exit_time: str, price_info: str) -> Dict[str, Any]:
    """
    MCP Sequential Thinking을 활용한 주차 요금 계산
    
    Args:
        entry_time: 입차 시간 (ISO format)
        exit_time: 출차 시간 (ISO format) 
        price_info: 가격 정보 문자열
        
    Returns:
        Dict[str, Any]: 계산 결과 및 단계별 사고 과정
    """
    try:
        # 시간 파싱
        entry_dt = datetime.fromisoformat(entry_time)
        exit_dt = datetime.fromisoformat(exit_time)
        
        # 경과 시간 계산 (분 단위)
        elapsed_minutes = int((exit_dt - entry_dt).total_seconds() / 60)
        
        # 단계별 사고 과정
        thinking_steps = []
        
        # 1단계: 기본 정보 확인
        thinking_steps.append({
            "step": 1,
            "description": "입차/출차 시간 분석",
            "details": {
                "entry_time": entry_time,
                "exit_time": exit_time,
                "elapsed_minutes": elapsed_minutes
            }
        })
        
        # 2단계: 요금 체계 분석
        thinking_steps.append({
            "step": 2,
            "description": "요금 체계 분석",
            "details": {
                "price_info": price_info,
                "free_period": "30분",
                "charge_period": "30분당 500원"
            }
        })
        
        # 3단계: 무료 시간 적용 여부 판단
        if elapsed_minutes <= 30:
            # 30분 이하: 무료
            thinking_steps.append({
                "step": 3,
                "description": "무료 시간 적용",
                "details": {
                    "reason": "30분 이하 주차",
                    "free_minutes": elapsed_minutes,
                    "chargeable_minutes": 0
                }
            })
            
            total_fee = 0
            chargeable_minutes = 0
            
        else:
            # 30분 초과: 요금 계산
            chargeable_minutes = elapsed_minutes - 30
            
            thinking_steps.append({
                "step": 3,
                "description": "요금 적용 시간 계산",
                "details": {
                    "free_minutes": 30,
                    "chargeable_minutes": chargeable_minutes,
                    "reason": "30분 초과 주차"
                }
            })
            
            # 4단계: 30분 단위 계산
            chargeable_30min_units = (chargeable_minutes + 29) // 30  # 올림 계산
            
            thinking_steps.append({
                "step": 4,
                "description": "30분 단위 계산",
                "details": {
                    "chargeable_minutes": chargeable_minutes,
                    "chargeable_30min_units": chargeable_30min_units,
                    "calculation": f"{chargeable_30min_units} × 500원"
                }
            })
            
            # 5단계: 총 요금 계산
            total_fee = chargeable_30min_units * 500
            
            thinking_steps.append({
                "step": 5,
                "description": "최종 요금 계산",
                "details": {
                    "chargeable_30min_units": chargeable_30min_units,
                    "unit_price": 500,
                    "total_fee": total_fee
                }
            })
        
        # 결과 반환
        result = {
            "success": True,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "elapsed_minutes": elapsed_minutes,
            "free_minutes": min(30, elapsed_minutes),
            "chargeable_minutes": max(0, elapsed_minutes - 30),
            "chargeable_30min_units": (max(0, elapsed_minutes - 30) + 29) // 30 if elapsed_minutes > 30 else 0,
            "total_fee": total_fee,
            "price_info": price_info,
            "thinking_steps": thinking_steps,
            "calculation_summary": {
                "is_free": elapsed_minutes <= 30,
                "free_period_used": min(30, elapsed_minutes),
                "charge_period": max(0, elapsed_minutes - 30),
                "final_amount": total_fee
            }
        }
        
        logger.info(f"주차 요금 계산 완료: {elapsed_minutes}분, {total_fee}원")
        return result
        
    except Exception as e:
        logger.error(f"주차 요금 계산 실패: {e}")
        return {
            "success": False,
            "error": str(e),
            "entry_time": entry_time,
            "exit_time": exit_time,
            "total_fee": 0
        }

def calculate_current_fee(entry_time: str, price_info: str) -> Dict[str, Any]:
    """
    현재 시간 기준 주차 요금 계산 (실시간)
    
    Args:
        entry_time: 입차 시간 (ISO format)
        price_info: 가격 정보 문자열
        
    Returns:
        Dict[str, Any]: 현재까지의 예상 요금
    """
    current_time = datetime.now().isoformat()
    return calculate_fee_with_thinking(entry_time, current_time, price_info)

def calculate_estimated_fee(entry_time: str, estimated_exit_time: str, price_info: str) -> Dict[str, Any]:
    """
    예상 출차시간 기준 주차 요금 계산
    
    Args:
        entry_time: 입차 시간 (ISO format)
        estimated_exit_time: 예상 출차시간 (ISO format)
        price_info: 가격 정보 문자열
        
    Returns:
        Dict[str, Any]: 예상 출차시간까지의 요금
    """
    return calculate_fee_with_thinking(entry_time, estimated_exit_time, price_info)

def format_estimated_fee_result(result: Dict[str, Any], estimated_exit_time: str) -> str:
    """
    예상 요금 계산 결과를 사용자 친화적 형식으로 포맷팅
    
    Args:
        result: calculate_estimated_fee 결과
        estimated_exit_time: 예상 출차시간
        
    Returns:
        str: 포맷팅된 결과 문자열
    """
    if not result.get("success", False):
        return f"❌ 예상 요금 계산 실패: {result.get('error', '알 수 없는 오류')}"
    
    elapsed_minutes = result["elapsed_minutes"]
    total_fee = result["total_fee"]
    free_minutes = result["free_minutes"]
    chargeable_minutes = result["chargeable_minutes"]
    
    # 예상 출차시간 포맷팅
    try:
        exit_dt = datetime.fromisoformat(estimated_exit_time)
        formatted_exit_time = exit_dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        formatted_exit_time = estimated_exit_time
    
    # 기본 정보
    output = f"🅿️ **예상 주차 요금 계산**\n"
    output += "=" * 50 + "\n\n"
    
    # 시간 정보
    output += f"⏰ **예상 출차시간**: {formatted_exit_time}\n"
    output += f"⏱️ **예상 주차 시간**: {elapsed_minutes}분\n"
    output += f"🆓 **무료 시간**: {free_minutes}분\n"
    if chargeable_minutes > 0:
        output += f"💰 **요금 시간**: {chargeable_minutes}분\n"
    
    # 요금 정보
    if total_fee == 0:
        output += f"✅ **예상 총 요금**: 무료 (30분 이하)\n"
    else:
        chargeable_units = result["chargeable_30min_units"]
        output += f"📊 **30분 단위**: {chargeable_units}개\n"
        output += f"💵 **예상 총 요금**: {total_fee:,}원\n"
    
    # 상세 계산 과정
    if result.get("thinking_steps"):
        output += "\n**📋 예상 요금 계산 과정:**\n"
        for step in result["thinking_steps"]:
            if step["step"] <= 3:  # 주요 단계만 표시
                output += f"- {step['description']}\n"
    
    return output

def format_fee_result(result: Dict[str, Any]) -> str:
    """
    요금 계산 결과를 사용자 친화적 형식으로 포맷팅
    
    Args:
        result: calculate_fee_with_thinking 결과
        
    Returns:
        str: 포맷팅된 결과 문자열
    """
    if not result.get("success", False):
        return f"❌ 요금 계산 실패: {result.get('error', '알 수 없는 오류')}"
    
    elapsed_minutes = result["elapsed_minutes"]
    total_fee = result["total_fee"]
    free_minutes = result["free_minutes"]
    chargeable_minutes = result["chargeable_minutes"]
    
    # 기본 정보
    output = f"🅿️ **주차 요금 계산 결과**\n"
    output += "=" * 50 + "\n\n"
    
    # 시간 정보
    output += f"⏰ **주차 시간**: {elapsed_minutes}분\n"
    output += f"🆓 **무료 시간**: {free_minutes}분\n"
    if chargeable_minutes > 0:
        output += f"💰 **요금 시간**: {chargeable_minutes}분\n"
    
    # 요금 정보
    if total_fee == 0:
        output += f"✅ **총 요금**: 무료 (30분 이하)\n"
    else:
        chargeable_units = result["chargeable_30min_units"]
        output += f"📊 **30분 단위**: {chargeable_units}개\n"
        output += f"💵 **총 요금**: {total_fee:,}원\n"
    
    # 상세 계산 과정 (간단 버전)
    if result.get("thinking_steps"):
        output += "\n**📋 계산 과정:**\n"
        for step in result["thinking_steps"]:
            if step["step"] <= 3:  # 주요 단계만 표시
                output += f"- {step['description']}\n"
    
    return output

def get_parking_duration_info(entry_time: str) -> Dict[str, Any]:
    """
    현재까지의 주차 시간 정보 조회
    
    Args:
        entry_time: 입차 시간 (ISO format)
        
    Returns:
        Dict[str, Any]: 주차 시간 정보
    """
    try:
        entry_dt = datetime.fromisoformat(entry_time)
        current_dt = datetime.now()
        
        elapsed_minutes = int((current_dt - entry_dt).total_seconds() / 60)
        elapsed_hours = elapsed_minutes // 60
        remaining_minutes = elapsed_minutes % 60
        
        return {
            "success": True,
            "entry_time": entry_time,
            "current_time": current_dt.isoformat(),
            "elapsed_minutes": elapsed_minutes,
            "elapsed_hours": elapsed_hours,
            "remaining_minutes": remaining_minutes,
            "formatted_duration": f"{elapsed_hours}시간 {remaining_minutes}분" if elapsed_hours > 0 else f"{elapsed_minutes}분"
        }
    except Exception as e:
        logger.error(f"주차 시간 정보 조회 실패: {e}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    # 테스트 코드
    print("=== 주차 요금 계산기 테스트 ===")
    
    # 기본 설정
    entry_time = "2024-01-01T10:00:00"
    price_info = "최초 30분 무료, 그후 30분당 500원"
    
    print(f"입차 시간: {entry_time}")
    print(f"요금 체계: {price_info}")
    print("=" * 60)
    
    # 사용자가 예상 출차시간을 입력하는 시뮬레이션
    print("\n=== 예상 출차시간 입력 테스트 ===")
    
    # 다양한 예상 출차시간 시나리오
    estimated_exit_times = [
        ("2024-01-01T10:25:00", "25분 후 출차 예정"),
        ("2024-01-01T10:30:00", "30분 후 출차 예정"),
        ("2024-01-01T10:45:00", "45분 후 출차 예정"),
        ("2024-01-01T11:00:00", "1시간 후 출차 예정"),
        ("2024-01-01T11:15:00", "1시간 15분 후 출차 예정"),
        ("2024-01-01T11:30:00", "1시간 30분 후 출차 예정"),
        ("2024-01-01T12:00:00", "2시간 후 출차 예정"),
        ("2024-01-01T13:00:00", "3시간 후 출차 예정"),
    ]
    
    for estimated_exit_time, description in estimated_exit_times:
        print(f"\n--- {description} ---")
        result = calculate_estimated_fee(entry_time, estimated_exit_time, price_info)
        
        if result['success']:
            elapsed_minutes = result['elapsed_minutes']
            total_fee = result['total_fee']
            free_minutes = result['free_minutes']
            chargeable_minutes = result['chargeable_minutes']
            chargeable_units = result['chargeable_30min_units']
            
            print(f"예상 출차시간: {estimated_exit_time}")
            print(f"예상 주차 시간: {elapsed_minutes}분")
            print(f"무료 시간: {free_minutes}분")
            print(f"요금 시간: {chargeable_minutes}분")
            print(f"30분 단위: {chargeable_units}개")
            print(f"예상 총 요금: {total_fee:,}원")
            
            # 요금 계산 과정 표시
            if total_fee == 0:
                print("→ 무료 (30분 이하)")
            else:
                print(f"→ {chargeable_units} × 500원 = {total_fee:,}원")
        else:
            print(f"오류: {result.get('error', '알 수 없는 오류')}")
    
    print("\n" + "=" * 60)
    print("=== 현재 시간 기준 테스트 ===")
    
    # 현재 시간 기준 테스트
    current_result = calculate_current_fee(entry_time, price_info)
    if current_result['success']:
        print(f"현재 시간 기준 경과: {current_result['elapsed_minutes']}분")
        print(f"현재 시간 기준 요금: {current_result['total_fee']:,}원")
    else:
        print(f"현재 시간 기준 오류: {current_result.get('error', '알 수 없는 오류')}")
    
    print("\n" + "=" * 60)
    print("=== 예상 출차시간 입력 시뮬레이션 ===")
    print("사용자가 예상 출차시간을 입력하면 해당 시점의 요금을 미리 계산할 수 있습니다.")
    print("예시: 2024-01-01T11:30:00 (1시간 30분 후 출차 예정)")
    
    # 사용자 입력 시뮬레이션
    test_exit_time = "2024-01-01T11:30:00"
    print(f"\n입력된 예상 출차시간: {test_exit_time}")
    
    estimated_result = calculate_estimated_fee(entry_time, test_exit_time, price_info)
    if estimated_result['success']:
        print(f"예상 주차 시간: {estimated_result['elapsed_minutes']}분")
        print(f"예상 총 요금: {estimated_result['total_fee']:,}원")
        print("→ 사용자가 미리 요금을 확인할 수 있습니다!")
    else:
        print(f"계산 오류: {estimated_result.get('error', '알 수 없는 오류')}")
