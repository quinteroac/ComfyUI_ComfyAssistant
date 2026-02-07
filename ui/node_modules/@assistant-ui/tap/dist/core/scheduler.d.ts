type Task = () => void;
export declare class UpdateScheduler {
    private readonly _task;
    private _isDirty;
    constructor(_task: Task);
    get isDirty(): boolean;
    markDirty(): void;
    runTask(): void;
}
export declare const flushResourcesSync: <T>(callback: () => T) => T;
export {};
//# sourceMappingURL=scheduler.d.ts.map