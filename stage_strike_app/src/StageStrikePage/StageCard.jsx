import {Box, Card, CardActionArea, CardMedia, Typography, GridLegacy as Grid} from "@mui/material";
import i18n from "i18next";

function GentlemanStamp() {
  return <>
    <div className="stamp stage-gentlemans"></div>
    <div className="banned_by">
      <Typography
        variant="button"
        component="div"
        fontWeight={"bold"}
        noWrap
        fontSize={{xs: 16, md: ""}}
      >
        {i18n.t("gentlemans")}
      </Typography>
    </div>
  </>
}

function SelectedStamp({currentPlayerName}) {
  return <>
    <div className="stamp stage-selected"></div>
    <div className="banned_by">
      <Typography
        variant="button"
        component="div"
        fontWeight={"bold"}
        noWrap
        fontSize={{xs: 16, md: ""}}
      >
        {currentPlayerName}
      </Typography>
    </div>
  </>
}

export function StageCard({
  stageName,
  stageImage,
  isSelected,
  onClick,
  isStriked,
  isBanned,
  strikedBy,
  isGentlemanEnabled,
  currentPlayerName,
}) {
  let borderColor = "lightgray";
  let boxShadow = "0 0 0px #ffffff00";

  if (isSelected) {
    borderColor = "#4caf50ff";
    boxShadow = "0 0 10px #4caf50ff";

    if (isStriked || isBanned) {
      borderColor = "#f44336ff";
      boxShadow = "0 0 10px #f44336ff"
    }
  }


  return <Grid item xs={4} sm={3} md={2}>
    <Card
      style={{
        borderStyle: "solid",
        borderWidth: 3,
        borderRadius: 8,
        borderColor: borderColor,
        boxShadow: boxShadow,
        transitionProperty: "border-color box-shadow",
        transitionDuration: "500ms",
      }}
    >
      <CardActionArea
        onClick={onClick}
      >
        { isStriked &&
          <>
            <div className="stamp stage-striked"></div>
            <div className="banned_by">
              <Typography
                variant="button"
                component="div"
                fontWeight={"bold"}
                noWrap
                fontSize={{xs: 16, md: ""}}
              >
                { strikedBy }
              </Typography>
            </div>
          </>
        }
        { isBanned && <div className="stamp stage-dsr"></div> }
        { isSelected &&
          <>
            { isGentlemanEnabled
              ? <GentlemanStamp />
              : <SelectedStamp currentPlayerName={currentPlayerName} />
            }
          </>
        }

        <CardMedia
          component="img"
          style={{aspectRatio: "3 / 2"}}
          image={stageImage}
        />
        <Box
          sx={{
            padding: {xs: "4px", sm: "6px", lg: "8px"},
          }}
        >
          <Typography
            variant="button"
            component="div"
            noWrap
            fontSize={{xs: 8, sm: 12, lg: ""}}
          >
            {stageName}
          </Typography>
        </Box>
      </CardActionArea>
    </Card>
  </Grid>
}
