import {Dialog, DialogContent, DialogTitle, Typography} from "@mui/material";
import {Box} from "@mui/system";
import i18n from "i18next";

export function NoRulesetError({currPlayer}) {
    return <>
        <Dialog
            open={currPlayer === -1}
            onClose={() => {
            }}
            aria-labelledby="modal-modal-title"
            aria-describedby="modal-modal-description"
        >
            <DialogTitle id="responsive-dialog-title">
                {i18n.t("title")}
            </DialogTitle>
            <DialogContent>
                <Box
                    component="div"
                    gap={2}
                    display="flex"
                    flexDirection={"column"}
                >
                    <Typography>{i18n.t("no_ruleset_error")}</Typography>
                </Box>
            </DialogContent>
        </Dialog>
    </>
}
