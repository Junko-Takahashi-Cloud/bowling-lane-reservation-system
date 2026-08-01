from datetime import date, time, timedelta

import streamlit as st

import api_client as api

st.set_page_config(page_title="スポーツボウリング場予約システム", page_icon="🎳", layout="centered")

# スポーツボウリング場予約システム — Streamlitフロントエンド
#
# 役割ごとに表示する画面を切り替える：
# - 未ログイン: ログイン / 新規登録
# - 一般利用者・競技者: 空き状況確認 / 予約登録 / 自分の予約確認・キャンセル
# - 管理者: 全予約確認・キャンセル / レーン管理
#
# トークン保持: st.session_state（ブラウザストレージは使わない。タブを閉じると再ログインが必要）

# ---------- セッション初期化 ----------
if "token" not in st.session_state:
    st.session_state.token = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "role" not in st.session_state:
    st.session_state.role = None


def logout():
    st.session_state.token = None
    st.session_state.user_name = None
    st.session_state.role = None


ROLE_LABELS = {"user": "一般利用者", "competitor": "競技者", "admin": "管理者"}
TYPE_LABELS = {"general": "一般利用", "practice": "競技者練習", "class": "初心者教室", "group": "レーン貸し切り（クラウドファンディング特典）"}


# ---------- 未ログイン: ログイン / 新規登録 ----------
def render_login_page():
    st.title("🎳 スポーツボウリング場予約システム")
    tab_login, tab_register = st.tabs(["ログイン", "新規登録"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("メールアドレス")
            password = st.text_input("パスワード", type="password")
            submitted = st.form_submit_button("ログイン")
        if submitted:
            ok, data = api.login(email, password)
            if ok:
                token = data["access_token"]
                me_ok, me_data = api.get_current_user(token)
                if me_ok:
                    st.session_state.token = token
                    st.session_state.role = me_data["role"]
                    st.session_state.user_name = me_data["name"]
                    st.rerun()
                else:
                    st.error(f"ユーザー情報の取得に失敗しました: {me_data}")
            else:
                st.error(f"ログインに失敗しました: {data}")

    with tab_register:
        with st.form("register_form"):
            name = st.text_input("氏名")
            reg_email = st.text_input("メールアドレス", key="reg_email")
            reg_password = st.text_input("パスワード（8文字以上推奨）", type="password", key="reg_password")
            role = st.selectbox("利用者種別", options=["user", "competitor"], format_func=lambda v: ROLE_LABELS[v])
            reg_submitted = st.form_submit_button("登録する")
        if reg_submitted:
            ok, data = api.register(name, reg_email, reg_password, role)
            if ok:
                st.success("登録が完了しました。ログインタブからログインしてください。")
            else:
                st.error(f"登録に失敗しました: {data}")


# ---------- 空き状況確認・予約登録 ----------
def render_reservation_page():
    st.header("📅 空き状況確認・予約")

    target_date = st.date_input("利用日", value=date.today(), min_value=date.today())
    ok, data = api.get_availability(target_date.isoformat())

    if not ok:
        st.error(f"空き状況の取得に失敗しました: {data}")
        return

    st.subheader("レーンセット状況")
    for ls in data["lane_sets"]:
        status_label = "🟢 利用可能" if ls["status"] == "available" else "🔧 メンテナンス中"
        st.write(f"**{ls['name']}**（{ls['lane_set_id']}）: {status_label}")

    if data["reservations"]:
        st.subheader(f"{target_date.isoformat()} の予約済み時間帯")
        for r in data["reservations"]:
            st.write(f"- {r['lane_set_id']}セット: {r['start_time']} 〜 {r['end_time']}")
    else:
        st.caption("この日の予約はまだありません。")

    st.divider()
    st.subheader("予約登録")

    available_lane_sets = [ls["lane_set_id"] for ls in data["lane_sets"] if ls["status"] == "available"]
    if not available_lane_sets:
        st.warning("現在利用可能なレーンセットがありません。")
        return

    reservation_type = st.selectbox(
        "予約種別", options=["general", "practice", "group"], format_func=lambda v: TYPE_LABELS[v]
    )

    contact_name = contact_email = contact_phone = None
    headcount = None
    if reservation_type == "general":
        st.caption("一般利用は初心者教室を修了した方のみご利用いただけます。")
    elif reservation_type == "group":
        st.caption("クラウドファンディング特典（レーン貸し切り）には代表者情報の入力が必要です。")
        contact_name = st.text_input("代表者氏名")
        contact_email = st.text_input("代表者メールアドレス")
        contact_phone = st.text_input("代表者電話番号（任意）")
        headcount = st.number_input("参加人数（任意）", min_value=0, step=1, value=0)

    with st.form("reservation_form"):
        lane_set_id = st.selectbox("レーンセット", options=available_lane_sets)
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.time_input("開始時間", value=time(10, 0), step=timedelta(minutes=30))
        with col2:
            end_time = st.time_input("終了時間", value=time(11, 0), step=timedelta(minutes=30))
        submitted = st.form_submit_button("予約する")

    if submitted:
        if reservation_type == "group":
            if not contact_name or not contact_email:
                st.error("団体予約には代表者氏名とメールアドレスの入力が必要です。")
                return
            ok, data = api.create_group_reservation(
                st.session_state.token,
                lane_set_id,
                target_date.isoformat(),
                start_time.strftime("%H:%M:%S"),
                end_time.strftime("%H:%M:%S"),
                contact_name,
                contact_email,
                contact_phone or None,
                int(headcount) if headcount else None,
            )
        else:
            ok, data = api.create_reservation(
                st.session_state.token,
                lane_set_id,
                target_date.isoformat(),
                start_time.strftime("%H:%M:%S"),
                end_time.strftime("%H:%M:%S"),
                reservation_type,
            )
        if ok:
            st.success("予約が完了しました。")
            st.rerun()
        else:
            st.error(f"予約に失敗しました: {data}")


# ---------- 初心者教室コース一覧・申込 ----------
def render_class_courses_page():
    st.header("🎓 初心者教室（全5回コース）")

    ok, courses = api.list_class_courses()
    if not ok:
        st.error(f"コース一覧の取得に失敗しました: {courses}")
        return

    if not courses:
        st.caption("現在開講中のコースはありません。")
        return

    day_labels = {
        "monday": "月", "tuesday": "火", "wednesday": "水", "thursday": "木",
        "friday": "金", "saturday": "土", "sunday": "日",
    }

    for c in courses:
        remaining = c["capacity"] - (c["enrolled_count"] or 0)
        with st.container(border=True):
            st.write(
                f"**毎週{day_labels.get(c['day_of_week'], c['day_of_week'])}曜日** "
                f"{c['start_time']}〜{c['end_time']}／{c['lane_set_id']}セット／講師: {c['instructor_name']}"
            )
            st.caption(
                f"初回: {c['first_date']}／全{c['session_count']}回／"
                f"空き {remaining} / {c['capacity']} 名"
            )
            if remaining > 0:
                if st.button("このコースに申し込む", key=f"enroll_{c['course_id']}"):
                    ok, result = api.enroll_class_course(st.session_state.token, c["course_id"])
                    if ok:
                        st.success("申し込みが完了しました。")
                        st.rerun()
                    else:
                        st.error(f"申し込みに失敗しました: {result}")
            else:
                st.warning("満員です。")

            if st.button("申し込みをキャンセル", key=f"cancel_enroll_{c['course_id']}"):
                ok, result = api.cancel_class_enrollment(st.session_state.token, c["course_id"])
                if ok:
                    st.success("キャンセルしました。")
                    st.rerun()
                else:
                    st.error(f"キャンセルに失敗しました: {result}")

            with st.expander("職場・グループでまとめて申し込む（人数上限なし）"):
                with st.form(f"group_enroll_form_{c['course_id']}"):
                    g_contact_name = st.text_input("代表者氏名", key=f"g_name_{c['course_id']}")
                    g_contact_email = st.text_input("代表者メールアドレス", key=f"g_email_{c['course_id']}")
                    g_contact_phone = st.text_input("代表者電話番号（任意）", key=f"g_phone_{c['course_id']}")
                    g_headcount = st.number_input("参加人数", min_value=1, step=1, value=1, key=f"g_head_{c['course_id']}")
                    g_submitted = st.form_submit_button("団体で申し込む")
                if g_submitted:
                    if not g_contact_name or not g_contact_email:
                        st.error("代表者氏名とメールアドレスの入力が必要です。")
                    else:
                        ok, result = api.enroll_class_course_group(
                            st.session_state.token, c["course_id"],
                            g_contact_name, g_contact_email, g_contact_phone or None, int(g_headcount),
                        )
                        if ok:
                            st.success("団体申込が完了しました。")
                            st.rerun()
                        else:
                            st.error(f"申し込みに失敗しました: {result}")


def render_my_reservations_page():
    st.header("🗒️ 自分の予約")
    ok, reservations = api.list_my_reservations(st.session_state.token)
    if not ok:
        st.error(f"予約一覧の取得に失敗しました: {reservations}")
        return

    if not reservations:
        st.caption("予約はまだありません。")
        return

    for r in reservations:
        status_label = "✅ 予約済" if r["status"] == "reserved" else "🚫 キャンセル済"
        with st.container(border=True):
            st.write(
                f"**{r['date']}** {r['start_time']}〜{r['end_time']} "
                f"／ {r['lane_set_id']}セット ／ {TYPE_LABELS.get(r['reservation_type'], r['reservation_type'])}"
            )
            st.caption(f"状態: {status_label}（予約ID: {r['reservation_id']}）")
            if r["status"] == "reserved":
                if st.button("この予約をキャンセル", key=f"cancel_{r['reservation_id']}"):
                    ok, result = api.cancel_reservation(st.session_state.token, r["reservation_id"])
                    if ok:
                        st.success("キャンセルしました。")
                        st.rerun()
                    else:
                        st.error(f"キャンセルに失敗しました: {result}")


# ---------- 管理者ダッシュボード ----------
def render_admin_page():
    st.header("🛠️ 管理者ダッシュボード")

    tab_reservations, tab_lanes = st.tabs(["全予約管理", "レーン管理"])

    with tab_reservations:
        ok, reservations = api.admin_list_reservations(st.session_state.token)
        if not ok:
            st.error(f"予約一覧の取得に失敗しました: {reservations}")
        elif not reservations:
            st.caption("予約はまだありません。")
        else:
            for r in reservations:
                status_label = "✅ 予約済" if r["status"] == "reserved" else "🚫 キャンセル済"
                with st.container(border=True):
                    st.write(
                        f"**{r['date']}** {r['start_time']}〜{r['end_time']} "
                        f"／ {r['lane_set_id']}セット ／ 利用者ID: {r['user_id']} "
                        f"／ {TYPE_LABELS.get(r['reservation_type'], r['reservation_type'])}"
                    )
                    st.caption(f"状態: {status_label}（予約ID: {r['reservation_id']}）")
                    if r["status"] == "reserved":
                        if st.button("管理者としてキャンセル", key=f"admin_cancel_{r['reservation_id']}"):
                            ok, result = api.admin_cancel_reservation(st.session_state.token, r["reservation_id"])
                            if ok:
                                st.success("キャンセルしました。")
                                st.rerun()
                            else:
                                st.error(f"キャンセルに失敗しました: {result}")

    with tab_lanes:
        ok, lanes = api.admin_list_lanes(st.session_state.token)
        if not ok:
            st.error(f"レーン情報の取得に失敗しました: {lanes}")
            return
        for ls in lanes:
            col1, col2 = st.columns([3, 2])
            with col1:
                current_status = "🟢 利用可能" if ls["status"] == "available" else "🔧 メンテナンス中"
                st.write(f"**{ls['name']}**（{ls['lane_set_id']}）: {current_status}")
            with col2:
                new_status = "maintenance" if ls["status"] == "available" else "available"
                label = "メンテナンス中にする" if ls["status"] == "available" else "利用可能に戻す"
                if st.button(label, key=f"lane_{ls['lane_set_id']}"):
                    ok, result = api.admin_update_lane_status(st.session_state.token, ls["lane_set_id"], new_status)
                    if ok:
                        st.rerun()
                    else:
                        st.error(f"更新に失敗しました: {result}")


# ---------- メイン ----------
def main():
    if st.session_state.token is None:
        render_login_page()
        return

    with st.sidebar:
        st.write(f"👤 ログイン中: {st.session_state.user_name}")
        if st.session_state.role == "admin":
            page = st.radio("メニュー", ["予約する", "教室に申し込む", "自分の予約", "管理者ダッシュボード"])
        else:
            page = st.radio("メニュー", ["予約する", "教室に申し込む", "自分の予約"])
        st.divider()
        if st.button("ログアウト"):
            logout()
            st.rerun()

    if page == "予約する":
        render_reservation_page()
    elif page == "教室に申し込む":
        render_class_courses_page()
    elif page == "自分の予約":
        render_my_reservations_page()
    elif page == "管理者ダッシュボード":
        render_admin_page()


if __name__ == "__main__":
    main()
