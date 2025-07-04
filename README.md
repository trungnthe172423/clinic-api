# clinic-api
POST /patients - Bệnh nhân tự tạo thông tin (không cần đăng nhập, trả về JWT).
GET /patients - Lấy danh sách bệnh nhân (chỉ nhân viên).
GET /patients/{id} - Lấy thông tin bệnh nhân (BOLA: Không kiểm tra quyền).
PUT /patients/{id} - Cập nhật thông tin bệnh nhân (BOLA: Cho phép cập nhật bệnh nhân khác).
DELETE /patients/{id} - Xóa bệnh nhân (BOLA: Cho phép xóa bệnh nhân khác).
POST /doctors - Tạo bác sĩ mới (chỉ nhân viên).
GET /doctors - Lấy danh sách bác sĩ.
GET /doctors/{id} - Lấy thông tin bác sĩ.
POST /staff - Tạo nhân viên mới (chỉ nhân viên).
GET /appointments - Lấy danh sách lịch hẹn (lọc theo vai trò).
GET /appointments/{id} - Lấy thông tin lịch hẹn (BOLA: Không kiểm tra quyền).
POST /appointments - Tạo lịch hẹn mới (bệnh nhân hoặc nhân viên).
PUT /appointments/{id} - Cập nhật lịch hẹn (BOLA: Cho phép cập nhật lịch hẹn khác).
DELETE /appointments/{id} - Hủy lịch hẹn (BOLA: Cho phép hủy lịch hẹn khác).
POST /prescriptions - Tạo đơn thuốc (chỉ bác sĩ).
