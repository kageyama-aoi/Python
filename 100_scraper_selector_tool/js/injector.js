function getXPath(element) {
    if (element.id !== '') {
        return 'id("' + element.id + '")';
    }
    if (element === document.body) {
        return element.tagName;
    }

    let ix = 0;
    const siblings = element.parentNode.childNodes;
    for (let i = 0; i < siblings.length; i++) {
        const sibling = siblings[i];
        if (sibling === element) {
            return getXPath(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']';
        }
        if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
            ix++;
        }
    }
}

document.body.addEventListener('click', function (e) {
    const tag = e.target.tagName;
    const id = e.target.id;
    const className = e.target.className;
    const xpath = getXPath(e.target);

    // 画面に表示されている文言を取得（優先順：value > innerText > alt）
    const label =
        e.target.value ||
        e.target.innerText ||
        e.target.alt ||
        "(テキストなし)";

    const logText = `クリック: ${tag} [${label.trim()}]｜ID:${id}｜Class:${className}｜XPath:${xpath}`;

    // 視覚的フィードバック（赤枠表示）
    const originalBorder = e.target.style.border;
    e.target.style.border = "3px solid red";
    setTimeout(() => {
        e.target.style.border = originalBorder;
    }, 500);

    // 本来のクリック動作（リンク遷移など）を無効化
    if (typeof PREVENT_NAVIGATION !== 'undefined' && PREVENT_NAVIGATION) {
        e.preventDefault();
        e.stopPropagation();
    }

    if (typeof MODE !== 'undefined' && MODE === 'log') {
        // Python側でログを拾うための目印として "TAG: " を付ける
        console.log("TAG: " + logText);
    } else {
        alert(logText);
    }
}, true);
