/**
 * This module contains data-modification functions for working with diffs generated via
 * the python DeepDiff library. The idea is that we have fairly heavily nested state
 * python-side, and we will be transmitted diffs as that state changes, to allow us to
 * avoid having to receive the entire state from the StateManager every time the state changes.
 *
 * Further, since we are using React, react requires an entirely new object to be created
 * on state updates, which is a large amount of memory to burn to change a single key in
 * an object 6 layers of nesting down. To solve this, we rely on the `immutability-helper` library,
 * which knows how to create "new" objects without re-allocating unchanged memory. Since React state
 * objects don't change, this is both safe and considered good practice. Basically we'll create
 * a nested "query" object and then tell the helper what update we'd like to perform.
 *
 * Here's an example of a python DeepDiff delta (docs: https://zepworks.com/deepdiff/current/delta.html):
 *
 * {
 *     "values_changed": {
 *         "root['foo']['bar']['baz']": {"new_value": "aaaa", "old_value": "bbbb"}
 *     },
 *     "dictionary_item_added": {
 *         "root['foo']['bar']['slop']: "new value here"
 *     },
 *     "dictionary_item_removed": {
 *         "root['foo']['bar']['notAnymore']": "deleted value here"
 *     }
 * }
 *
 * Here's an example of a immutability-helper update query from the above
 *
 * {
 *     foo: {
 *         bar: {
 *           baz: {
 *               "$set": "aaaa"
 *           },
 *           slop: {
 *               "$set": "new value here"
 *           }
 *           "$unset": ["notAnymore"]
 *         }
 *     }
 * }
 *
 * And if we had an existing state structure that looked like this:
 * {
 *     foo: {
 *         bar: {
 *             baz: "bbbb"
 *             notAnymore: "oh no"
 *         }
 *     }
 * }
 *
 * We would expect it to turn into the following:
 *
 * {
 *     foo: {
 *         bar: {
 *             baz: "aaaa"
 *             slop: "new value here"
 *         }
 *     }
 * }
 *
 */

/** @typedef {'values_changed'|'dictionary_item_added'|'dictionary_item_removed'} DiffOperation */
/** @typedef {Object} ImmutabilityHelperQuery */
/**
 * @typedef {{
 *   [DiffOperation]: Record.<str, any>
 * }} Diff
 */

/** @typedef {{
 *   action: DeltaOpType,
 *   path: (string|number)[]
 *   type: string
 *   value: any
 * }} Delta
 */

/**
 * @typedef {(
 *    "type_changes"
 *  | "values_changed"
 *  | "dictionary_item_added"
 *  | "dictionary_item_removed"
 *  | "iterable_item_added"
 *  | "iterable_item_removed"
 *  | "attribute_added"
 *  | "attribute_removed"
 *  | "set_item_added"
 *  | "set_item_removed"
 *  | "repetition_change"
 * )} DeltaOpType
 */

/**
 * Takes a single diff operation, and adds it to an existing query object.
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
