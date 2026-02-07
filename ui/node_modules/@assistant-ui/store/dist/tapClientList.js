import { tapConst, tapState, withKey } from "@assistant-ui/tap";
import { tapClientLookup } from "./tapClientLookup.js";
const createProps = (key, data, remove) => {
    return {
        key,
        getInitialData: () => {
            if (!data.hasData) {
                throw new Error("getInitialData may only be called during initial render");
            }
            return data.data;
        },
        remove,
    };
};
export const tapClientList = (props) => {
    const { initialValues, getKey, resource: Resource } = props;
    const initialDataHandles = tapConst(() => [], []);
    const [items, setItems] = tapState(() => {
        const entries = [];
        for (const data of initialValues) {
            const key = getKey(data);
            const handle = { data, hasData: true };
            entries.push([
                key,
                createProps(key, handle, () => {
                    setItems((items) => {
                        const newItems = { ...items };
                        delete newItems[key];
                        return newItems;
                    });
                }),
            ]);
            initialDataHandles.push(handle);
        }
        return Object.fromEntries(entries);
    });
    const lookup = tapClientLookup(() => Object.values(items).map((props) => withKey(props.key, Resource(props))), [items, Resource]);
    initialDataHandles.forEach((handle) => {
        handle.data = undefined;
        handle.hasData = false;
    });
    const add = (data) => {
        const key = getKey(data);
        setItems((items) => {
            if (key in items) {
                throw new Error(`Tried to add item with a key ${key} that already exists`);
            }
            const handle = { data, hasData: true };
            initialDataHandles.push(handle);
            return {
                ...items,
                [key]: createProps(key, handle, () => {
                    setItems((items) => {
                        const newItems = { ...items };
                        delete newItems[key];
                        return newItems;
                    });
                }),
            };
        });
    };
    return {
        state: lookup.state,
        get: lookup.get,
        add,
    };
};
//# sourceMappingURL=tapClientList.js.map