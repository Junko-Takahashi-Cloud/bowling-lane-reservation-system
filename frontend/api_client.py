"""
バックエンドAPI呼び出しのラッパー

エラーハンドリング方針：
- 4xx/5xxは例外を投げず、(成功可否, データ or エラーメッセージ) のタプルで返す
  → Streamlit側でst.error()等に直接渡しやすくするため
"""
import os
import requests

API_BASE_URL = os.environ.get("BOWLING_API_BASE_URL", "http://127.0.0.1:8000")


def _handle(resp: requests.Response):
    if resp.ok:
        return True, resp.json() if resp.content else None
    try:
        detail = resp.json().get("detail", resp.text)
    except Exception:
        detail = resp.text
    return False, detail


def register(name: str, email: str, password: str, role: str = "user"):
    resp = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"name": name, "email": email, "password": password, "role": role},
    )
    return _handle(resp)


def login(email: str, password: str):
    resp = requests.post(
        f"{API_BASE_URL}/auth/login",
        data={"username": email, "password": password},
    )
    return _handle(resp)


def _auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def get_current_user(token: str):
    resp = requests.get(f"{API_BASE_URL}/auth/me", headers=_auth_headers(token))
    return _handle(resp)


def get_availability(target_date: str):
    resp = requests.get(f"{API_BASE_URL}/reservations/availability", params={"target_date": target_date})
    return _handle(resp)


def create_reservation(token: str, lane_set_id: str, date: str, start_time: str, end_time: str, reservation_type: str):
    resp = requests.post(
        f"{API_BASE_URL}/reservations",
        headers=_auth_headers(token),
        json={
            "lane_set_id": lane_set_id,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "reservation_type": reservation_type,
        },
    )
    return _handle(resp)


def create_group_reservation(
    token: str, lane_set_id: str, date: str, start_time: str, end_time: str,
    contact_name: str, contact_email: str, contact_phone: str = None, headcount: int = None,
):
    resp = requests.post(
        f"{API_BASE_URL}/reservations/group",
        headers=_auth_headers(token),
        json={
            "lane_set_id": lane_set_id,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "contact_name": contact_name,
            "contact_email": contact_email,
            "contact_phone": contact_phone,
            "headcount": headcount,
        },
    )
    return _handle(resp)


def list_class_courses():
    resp = requests.get(f"{API_BASE_URL}/class-courses")
    return _handle(resp)


def enroll_class_course(token: str, course_id: int):
    resp = requests.post(f"{API_BASE_URL}/class-courses/{course_id}/enroll", headers=_auth_headers(token))
    return _handle(resp)


def enroll_class_course_group(
    token: str, course_id: int, contact_name: str, contact_email: str,
    contact_phone: str = None, headcount: int = None,
):
    resp = requests.post(
        f"{API_BASE_URL}/class-courses/{course_id}/enroll-group",
        headers=_auth_headers(token),
        json={
            "contact_name": contact_name,
            "contact_email": contact_email,
            "contact_phone": contact_phone,
            "headcount": headcount,
        },
    )
    return _handle(resp)


def cancel_class_enrollment(token: str, course_id: int):
    resp = requests.delete(f"{API_BASE_URL}/class-courses/{course_id}/enroll", headers=_auth_headers(token))
    return _handle(resp)


def list_my_reservations(token: str):
    resp = requests.get(f"{API_BASE_URL}/reservations/me", headers=_auth_headers(token))
    return _handle(resp)


def cancel_reservation(token: str, reservation_id: int):
    resp = requests.delete(f"{API_BASE_URL}/reservations/{reservation_id}", headers=_auth_headers(token))
    return _handle(resp)


def admin_list_reservations(token: str):
    resp = requests.get(f"{API_BASE_URL}/admin/reservations", headers=_auth_headers(token))
    return _handle(resp)


def admin_cancel_reservation(token: str, reservation_id: int):
    resp = requests.delete(f"{API_BASE_URL}/admin/reservations/{reservation_id}", headers=_auth_headers(token))
    return _handle(resp)


def admin_list_lanes(token: str):
    resp = requests.get(f"{API_BASE_URL}/admin/lanes", headers=_auth_headers(token))
    return _handle(resp)


def admin_update_lane_status(token: str, lane_set_id: str, status_value: str):
    resp = requests.patch(
        f"{API_BASE_URL}/admin/lanes/{lane_set_id}",
        headers=_auth_headers(token),
        json={"status": status_value},
    )
    return _handle(resp)
