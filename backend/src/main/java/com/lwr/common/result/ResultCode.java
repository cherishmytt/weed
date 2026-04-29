package com.lwr.common.result;

import lombok.Getter;

/**
 * 统一返回错误码
 */
@Getter
public enum ResultCode {

    SUCCESS(200, "请求成功"),
    BAD_REQUEST(400, "请求参数错误"),
    UNAUTHORIZED(401, "未登录或Token失效"),
    FORBIDDEN(403, "权限不足"),
    NOT_FOUND(404, "资源不存在"),
    INTERNAL_ERROR(500, "服务器内部错误"),

    // 认证相关 1xxx
    LOGIN_FAILED(1001, "用户名或密码错误"),
    USERNAME_EXISTS(1002, "用户名已存在"),

    // 检测相关 3xxx
    DETECTION_SERVICE_UNAVAILABLE(3001, "检测服务不可用"),
    INVALID_IMAGE_FORMAT(3002, "图片格式不支持");

    private final Integer code;
    private final String message;

    ResultCode(Integer code, String message) {
        this.code = code;
        this.message = message;
    }
}
