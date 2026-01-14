#!/bin/bash
# 鍓嶇瀹瑰櫒鍚姩鑴氭湰
# 鏀寔nginx閰嶇疆鏂囦欢鍙屽悜鍚屾:浼樺厛浣跨敤澶栭儴閰嶇疆,涓嶅瓨鍦ㄦ椂浠庨暅鍍忓鍒跺埌澶栭儴

set -e

echo "=========================================="
echo "馃殌 浠撳簱绠＄悊绯荤粺鍓嶇瀹瑰櫒鍚姩"
echo "=========================================="

# 瀹氫箟棰滆壊
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# nginx閰嶇疆鏂囦欢璺緞锛堢洰褰曟寕杞斤級
EXTERNAL_NGINX_CONF="/etc/nginx/conf-external/nginx.conf"  # 鎸傝浇鐩綍涓殑閰嶇疆鏂囦欢
TEMPLATE_NGINX_CONF="/etc/nginx/nginx.conf.template"      # 闀滃儚鍐呯殑妯℃澘鏂囦欢
DEFAULT_NGINX_CONF="/etc/nginx/nginx.conf.default"       # 闀滃儚鍐呯殑榛樿閰嶇疆
NGINX_ACTIVE_CONF="/etc/nginx/nginx.conf"                # nginx瀹為檯浣跨敤鐨勯厤缃?
echo ""
echo "馃攳 妫€鏌ginx閰嶇疆鏂囦欢..."

# 妫€鏌ユ寕杞界洰褰曟槸鍚﹀彲璁块棶
if [ ! -d "/etc/nginx/conf-external" ]; then
    echo -e "${YELLOW}鈿狅笍  鎸傝浇鐩綍涓嶅瓨鍦紝浣跨敤榛樿閰嶇疆${NC}"
    cp "$DEFAULT_NGINX_CONF" "$NGINX_ACTIVE_CONF" 2>/dev/null || true
else
    # 妫€鏌ュ閮ㄦ寕杞界殑閰嶇疆鏂囦欢鏄惁瀛樺湪
    if [ -f "$EXTERNAL_NGINX_CONF" ]; then
        # 妫€鏌ユ枃浠跺ぇ灏?鍒ゆ柇鏄惁鏄湁鏁堢殑閰嶇疆鏂囦欢(涓嶆槸绌烘枃浠舵垨鐩綍)
        # 鍏煎涓嶅悓绯荤粺鐨剆tat鍛戒护鏍煎紡
        FILE_SIZE=$(stat -f%z "$EXTERNAL_NGINX_CONF" 2>/dev/null || stat -c%s "$EXTERNAL_NGINX_CONF" 2>/dev/null || echo 0)
        
        if [ "$FILE_SIZE" -gt 100 ]; then
            # 瀹夸富鏈哄凡鏈夐厤缃枃浠?            echo -e "${GREEN}鉁?浣跨敤瀹夸富鏈虹殑nginx閰嶇疆鏂囦欢${NC}"
            echo "   璺緞: $EXTERNAL_NGINX_CONF"
            echo "   澶у皬: $FILE_SIZE bytes"
            
            # 楠岃瘉閰嶇疆鏂囦欢璇硶
            if nginx -t -c "$EXTERNAL_NGINX_CONF" 2>/dev/null; then
                echo -e "${GREEN}鉁?nginx閰嶇疆璇硶楠岃瘉閫氳繃${NC}"
                # 澶嶅埗鍒皀ginx瀹為檯浣跨敤鐨勪綅缃?                cp "$EXTERNAL_NGINX_CONF" "$NGINX_ACTIVE_CONF"
            else
                echo -e "${YELLOW}鈿狅笍  nginx閰嶇疆璇硶閿欒${NC}"
                echo -e "${YELLOW}   灏嗕娇鐢ㄩ暅鍍忔ā鏉胯鐩?{NC}"
                # 璇硶閿欒鏃?鐢ㄦā鏉胯鐩?                if [ -f "$TEMPLATE_NGINX_CONF" ]; then
                    cp "$TEMPLATE_NGINX_CONF" "$EXTERNAL_NGINX_CONF" 2>/dev/null || true
                    cp "$TEMPLATE_NGINX_CONF" "$NGINX_ACTIVE_CONF"
                    echo -e "${GREEN}鉁?宸蹭粠闀滃儚妯℃澘瑕嗙洊nginx閰嶇疆鏂囦欢${NC}"
                fi
            fi
        else
            # 鏂囦欢瀛樺湪浣嗘棤鏁?鍙兘鏄惎鍔ㄨ剼鏈垱寤虹殑绌烘枃浠?
            echo -e "${YELLOW}鈿狅笍  澶栭儴閰嶇疆鏂囦欢鏃犳晥锛屼粠闀滃儚澶嶅埗${NC}"
            echo "   鏂囦欢澶у皬: $FILE_SIZE bytes"
            
            # 浠庨暅鍍忔ā鏉垮鍒堕厤缃枃浠跺埌澶栭儴鎸傝浇鐩綍
            if [ -f "$TEMPLATE_NGINX_CONF" ]; then
                if cp "$TEMPLATE_NGINX_CONF" "$EXTERNAL_NGINX_CONF" 2>/dev/null; then
                    echo -e "${GREEN}鉁?宸蹭粠闀滃儚澶嶅埗nginx閰嶇疆鏂囦欢鍒版寕杞界洰褰?{NC}"
                    echo "   婧? $TEMPLATE_NGINX_CONF"
                    echo "   鐩爣: $EXTERNAL_NGINX_CONF"
                    # 鍚屾椂澶嶅埗鍒皀ginx瀹為檯浣跨敤鐨勪綅缃?                    cp "$TEMPLATE_NGINX_CONF" "$NGINX_ACTIVE_CONF"
                else
                    echo -e "${YELLOW}鈿狅笍  鏃犳硶鍐欏叆鎸傝浇鐩綍(鏉冮檺涓嶈冻)${NC}"
                    echo -e "${YELLOW}   灏嗕娇鐢ㄩ粯璁ら厤缃?{NC}"
                    cp "$DEFAULT_NGINX_CONF" "$NGINX_ACTIVE_CONF" 2>/dev/null || true
                fi
            else
                echo -e "${YELLOW}鈿狅笍  闀滃儚涓病鏈夋ā鏉?浣跨敤榛樿閰嶇疆${NC}"
                cp "$DEFAULT_NGINX_CONF" "$NGINX_ACTIVE_CONF" 2>/dev/null || true
            fi
        fi
    else
        # 澶栭儴閰嶇疆鏂囦欢涓嶅瓨鍦紝浠庨暅鍍忓鍒?        echo -e "${YELLOW}鈿狅笍  澶栭儴nginx閰嶇疆鏂囦欢涓嶅瓨鍦紝浠庨暅鍍忓鍒?{NC}"
        
        if [ -f "$TEMPLATE_NGINX_CONF" ]; then
            # 妫€鏌ユ寕杞界洰褰曟槸鍚﹀彲鍐?            if [ ! -w "/etc/nginx/conf-external" ]; then
                echo -e "${YELLOW}鈿狅笍  /etc/nginx/conf-external 鐩綍涓嶅彲鍐?{NC}"
                echo "   褰撳墠鐢ㄦ埛: $(whoami) (UID: $(id -u))"
                echo "   鐩綍鏉冮檺: $(ls -ld /etc/nginx/conf-external)"
                echo -e "${YELLOW}   浣跨敤榛樿閰嶇疆${NC}"
                cp "$DEFAULT_NGINX_CONF" "$NGINX_ACTIVE_CONF" 2>/dev/null || true
            else
                # 灏濊瘯澶嶅埗鏂囦欢鍒版寕杞界洰褰?                if cp "$TEMPLATE_NGINX_CONF" "$EXTERNAL_NGINX_CONF" 2>/dev/null; then
                    echo -e "${GREEN}鉁?宸蹭粠闀滃儚澶嶅埗nginx閰嶇疆鏂囦欢鍒版寕杞界洰褰?{NC}"
                    echo "   婧? $TEMPLATE_NGINX_CONF"
                    echo "   鐩爣: $EXTERNAL_NGINX_CONF"
                    # 鍚屾椂澶嶅埗鍒皀ginx瀹為檯浣跨敤鐨勪綅缃?                    cp "$TEMPLATE_NGINX_CONF" "$NGINX_ACTIVE_CONF"
                else
                    echo -e "${YELLOW}鈿狅笍  鏃犳硶澶嶅埗閰嶇疆鏂囦欢锛堟潈闄愪笉瓒筹級${NC}"
                    echo -e "${YELLOW}   浣跨敤榛樿閰嶇疆${NC}"
                    cp "$DEFAULT_NGINX_CONF" "$NGINX_ACTIVE_CONF" 2>/dev/null || true
                fi
            fi
        else
            echo -e "${YELLOW}鈿狅笍  闀滃儚涓病鏈夋ā鏉?浣跨敤榛樿閰嶇疆${NC}"
            cp "$DEFAULT_NGINX_CONF" "$NGINX_ACTIVE_CONF" 2>/dev/null || true
        fi
    fi
fi

echo ""
echo "馃攳 妫€鏌ginx閰嶇疆..."
nginx -t -c "$NGINX_ACTIVE_CONF"

echo ""
echo "馃殌 鍚姩nginx鏈嶅姟..."
exec "$@"