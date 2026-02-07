"use client";
import { useComposedRefs } from "@radix-ui/react-compose-refs";
import { useCallback, useRef } from "react";
import { useAuiEvent } from "@assistant-ui/store";
import { useOnResizeContent } from "../../utils/hooks/useOnResizeContent.js";
import { useOnScrollToBottom } from "../../utils/hooks/useOnScrollToBottom.js";
import { useManagedRef } from "../../utils/hooks/useManagedRef.js";
import { writableStore } from "../../context/ReadonlyStore.js";
import { useThreadViewportStore } from "../../context/react/ThreadViewportContext.js";
export const useThreadViewportAutoScroll = ({ autoScroll, scrollToBottomOnRunStart = true, scrollToBottomOnInitialize = true, scrollToBottomOnThreadSwitch = true, }) => {
    const divRef = useRef(null);
    const threadViewportStore = useThreadViewportStore();
    if (autoScroll === undefined) {
        autoScroll = threadViewportStore.getState().turnAnchor !== "top";
    }
    const lastScrollTop = useRef(0);
    // bug: when ScrollToBottom's button changes its disabled state, the scroll stops
    // fix: delay the state change until the scroll is done
    // stores the scroll behavior to reuse during content resize, or null if not scrolling
    const scrollingToBottomBehaviorRef = useRef(null);
    const scrollToBottom = useCallback((behavior) => {
        const div = divRef.current;
        if (!div)
            return;
        scrollingToBottomBehaviorRef.current = behavior;
        div.scrollTo({ top: div.scrollHeight, behavior });
    }, []);
    const handleScroll = () => {
        const div = divRef.current;
        if (!div)
            return;
        const isAtBottom = threadViewportStore.getState().isAtBottom;
        const newIsAtBottom = Math.abs(div.scrollHeight - div.scrollTop - div.clientHeight) < 1 ||
            div.scrollHeight <= div.clientHeight;
        if (!newIsAtBottom && lastScrollTop.current < div.scrollTop) {
            // ignore scroll down
        }
        else {
            if (newIsAtBottom) {
                scrollingToBottomBehaviorRef.current = null;
            }
            const shouldUpdate = newIsAtBottom || scrollingToBottomBehaviorRef.current === null;
            if (shouldUpdate && newIsAtBottom !== isAtBottom) {
                writableStore(threadViewportStore).setState({
                    isAtBottom: newIsAtBottom,
                });
            }
        }
        lastScrollTop.current = div.scrollTop;
    };
    const resizeRef = useOnResizeContent(() => {
        const scrollBehavior = scrollingToBottomBehaviorRef.current;
        if (scrollBehavior) {
            scrollToBottom(scrollBehavior);
        }
        else if (autoScroll && threadViewportStore.getState().isAtBottom) {
            scrollToBottom("instant");
        }
        handleScroll();
    });
    const scrollRef = useManagedRef((el) => {
        el.addEventListener("scroll", handleScroll);
        return () => {
            el.removeEventListener("scroll", handleScroll);
        };
    });
    useOnScrollToBottom(({ behavior }) => {
        scrollToBottom(behavior);
    });
    // autoscroll on run start
    useAuiEvent("thread.runStart", () => {
        if (!scrollToBottomOnRunStart)
            return;
        scrollingToBottomBehaviorRef.current = "auto";
        requestAnimationFrame(() => {
            scrollToBottom("auto");
        });
    });
    // scroll to bottom instantly when thread history is first loaded
    useAuiEvent("thread.initialize", () => {
        if (!scrollToBottomOnInitialize)
            return;
        scrollingToBottomBehaviorRef.current = "instant";
        requestAnimationFrame(() => {
            scrollToBottom("instant");
        });
    });
    // scroll to bottom instantly when switching threads
    useAuiEvent("threadListItem.switchedTo", () => {
        if (!scrollToBottomOnThreadSwitch)
            return;
        scrollingToBottomBehaviorRef.current = "instant";
        requestAnimationFrame(() => {
            scrollToBottom("instant");
        });
    });
    const autoScrollRef = useComposedRefs(resizeRef, scrollRef, divRef);
    return autoScrollRef;
};
//# sourceMappingURL=useThreadViewportAutoScroll.js.map