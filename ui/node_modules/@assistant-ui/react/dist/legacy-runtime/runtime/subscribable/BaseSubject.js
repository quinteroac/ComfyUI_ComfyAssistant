export class BaseSubject {
    _subscriptions = new Set();
    _connection;
    get isConnected() {
        return !!this._connection;
    }
    notifySubscribers() {
        for (const callback of this._subscriptions)
            callback();
    }
    _updateConnection() {
        if (this._subscriptions.size > 0) {
            if (this._connection)
                return;
            this._connection = this._connect();
        }
        else {
            this._connection?.();
            this._connection = undefined;
        }
    }
    subscribe(callback) {
        this._subscriptions.add(callback);
        this._updateConnection();
        return () => {
            this._subscriptions.delete(callback);
            this._updateConnection();
        };
    }
}
//# sourceMappingURL=BaseSubject.js.map