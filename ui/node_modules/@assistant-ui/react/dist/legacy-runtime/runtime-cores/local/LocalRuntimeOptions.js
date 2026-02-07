export const splitLocalRuntimeOptions = (options) => {
    const { cloud, initialMessages, maxSteps, adapters, unstable_humanToolNames, ...rest } = options;
    return {
        localRuntimeOptions: {
            cloud,
            initialMessages,
            maxSteps,
            adapters,
            unstable_humanToolNames,
        },
        otherOptions: rest,
    };
};
//# sourceMappingURL=LocalRuntimeOptions.js.map