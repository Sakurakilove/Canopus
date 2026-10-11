-- Exact RW6 profile: restricted signed installer endpoint; native Manager
-- remains the owner of enable/activate operations.
local ENDPOINT, REPLY_SIZE = "/canopus/install", 40
local SUPERVISOR_MISSING = "请先打开 Canopus RW6 启动入口"
local BUILD_PROPERTY = "ro.build.id"
local function fallback_identity() return nil, nil end
local function prepare_inbox(checkpoint)
    checkpoint("准备模块安装目录")
    os.execute("mkdir /data/canopus")
    os.execute("mkdir /data/canopus/inbox")
end
local function failure_detail(response)
    return " error " .. string.unpack("<i4", response, 37)
end
