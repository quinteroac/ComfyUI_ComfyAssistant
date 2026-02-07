export class AttachmentRuntimeImpl {
    _core;
    get path() {
        return this._core.path;
    }
    constructor(_core) {
        this._core = _core;
        this.__internal_bindMethods();
    }
    __internal_bindMethods() {
        this.getState = this.getState.bind(this);
        this.remove = this.remove.bind(this);
        this.subscribe = this.subscribe.bind(this);
    }
    getState() {
        return this._core.getState();
    }
    subscribe(callback) {
        return this._core.subscribe(callback);
    }
}
class ComposerAttachmentRuntime extends AttachmentRuntimeImpl {
    _composerApi;
    constructor(core, _composerApi) {
        super(core);
        this._composerApi = _composerApi;
    }
    remove() {
        const core = this._composerApi.getState();
        if (!core)
            throw new Error("Composer is not available");
        return core.removeAttachment(this.getState().id);
    }
}
export class ThreadComposerAttachmentRuntimeImpl extends ComposerAttachmentRuntime {
    get source() {
        return "thread-composer";
    }
}
export class EditComposerAttachmentRuntimeImpl extends ComposerAttachmentRuntime {
    get source() {
        return "edit-composer";
    }
}
export class MessageAttachmentRuntimeImpl extends AttachmentRuntimeImpl {
    get source() {
        return "message";
    }
    constructor(core) {
        super(core);
    }
    remove() {
        throw new Error("Message attachments cannot be removed");
    }
}
//# sourceMappingURL=AttachmentRuntime.js.map