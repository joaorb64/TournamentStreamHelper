/**
 * This module contains data-modification functions for working with diffs generated via
 * the python DeepDiff library. The idea is that we have fairly heavily nested state
 * python-side, and we will be transmitted diffs as that state changes, to allow us to
 * avoid having to receive the entire state from the StateManager every time the state changes.
 *
 * Further, since we are using React, react requires an entirely new object to be created
 * on state updates, which is a large amount of memory to burn to change a single key in
 * an object 6 layers of nesting down. To solve this, we rely on the `immer` library,
 * which knows how to create "new" objects without re-allocating unchanged memory. Since React state
 * objects don't change, this is both safe and considered good practice. Basically
 * the way it works is that immer creates a "draft" object, which is very similar to a
 * recording mock used for unit tests. Once you modify the draft object, immer
 * will create a new object that shares memory with the old object where possible.
 *
 * It's worth mentioning that we depend on using the **Delta** portion of python's DeepDiff library.
 * using the deltas makes it specify every changed scalar rather than grouping things into
 * objects that get added, which complicates things dramatically when trying to batch updates.
 */

/**
 * Takes a single delta operation, and modifies the data object.
 *
 * @param {Object} data
 * @param {Delta} delta
 */
export function applyDelta(data, delta) {
    const pathPieces = delta.path;
    /** @type {DeltaOpType} */ const deltaOp = delta.action;
    const newValue = delta.value;
    const lastPiece = pathPieces[pathPieces.length-1];

    let currentData = data;
    for (let i = 0; i < pathPieces.length-1; i += 1) {
        if (!currentData.hasOwnProperty(pathPieces[i])) {
            currentData[pathPieces[i]] = {};
        }

        currentData = currentData[pathPieces[i]];
    }

    if (deltaOp === 'dictionary_item_removed') {
        if (currentData.hasOwnProperty(lastPiece)) {
            delete currentData[lastPiece];
        } else {
            console.warn(`Couldn't find data to delete for path: ${pathPieces}`);
        }
    } else {
        currentData[lastPiece] = newValue;
    }
}

/**
 * @param {Object} data
 * @param {Delta[]} deltas python deep-diff delta object.
 */
export function applyDeltas(data, deltas) {
    for (let delta of deltas) {
        applyDelta(data, delta);
    }

    return data;
}

/**
 * Useful function for printing and debugging.
 */
export function combineDeltas(/** Delta[] */ deltas) {
    const megaDiff = {};

    for (let delta of deltas) {
        if (!megaDiff.hasOwnProperty(delta.action)) {
            megaDiff[delta.action] = {};
        }

        megaDiff[delta.action][delta.path.join('.')] = {value: delta.value, type: delta.type};
    }

    return megaDiff;
}
