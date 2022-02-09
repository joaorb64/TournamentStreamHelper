import logo from './logo.svg';
import './App.css';
import { Component } from 'react';

class App extends Component {
  state = {
    ruleset: null,
    currGame: 0,
    currPlayer: 0,
    currStep: 0,
    strikedStages: [],
    stagesWon: [[],[]],
    stagesPicked: [],
    selectedStage: null,
    lastWinner: -1
  };

  Initialize(){
    this.setState({
      currGame: 0,
      currPlayer: 0,
      currStep: 0,
      strikedStages: [[]],
      stagesWon: [[],[]],
      stagesPicked: [],
      selectedStage: null,
      lastWinner: -1
    })
  }

  GetStage(stage){
    let found = this.state.ruleset.neutralStages.find((s)=>s.name === stage);
    if(found) return found;
    found = this.state.ruleset.counterpickStages.find((s)=>s.name === stage);
    if(found) return found;
    return null;
  }

  IsStageStriked(stage, previously=false){
    for(let i=0; i<Object.values(this.state.strikedStages).length; i+=1){
      if(i === Object.values(this.state.strikedStages).length-1 && previously){
        continue;
      }
      let round = Object.values(this.state.strikedStages)[i];
      let found = round.findIndex((e)=>e === stage);
      if(found !== -1){
        return true;
      }
    }
    return false;
  }

  GetBannedStages(){
    let banList = [];

    if(this.state.ruleset.useDSR){
      banList = this.state.stagesPicked;
    } else if(this.state.ruleset.useMDSR && this.state.lastWinner !== -1){
      banList = this.state.stagesWon[(this.state.lastWinner+1)%2];
    }

    return banList;
  }

  IsStageBanned(stage){
    let banList = this.GetBannedStages();

    let found = banList.findIndex((e)=>e === stage);
    if(found !== -1){
      return true;
    }
    return false;
  }

  StageClicked(stage){
    if(this.state.currGame > 0 && this.state.currStep > 0){
      // pick
      if(!this.IsStageBanned(stage.name) && !this.IsStageStriked(stage.name)){
        this.state.selectedStage = stage.name;
        this.setState(this.state);
      }
    } else if(!this.IsStageStriked(stage.name, true) && !this.IsStageBanned(stage.name)){
      // ban
      let foundIndex = this.state.strikedStages[this.state.currStep].findIndex((e)=>e === stage.name);
      if(foundIndex === -1){
        if(this.state.strikedStages[this.state.currStep].length < this.GetStrikeNumber()){
          this.state.strikedStages[this.state.currStep].push(stage.name);
        }
      } else {
        this.state.strikedStages[this.state.currStep].splice(foundIndex, 1)
      }
      this.setState(this.state);
    }
  }

  ConfirmClicked(){
    if(this.state.currGame == 0){
      if(this.state.strikedStages[this.state.currStep].length === this.state.ruleset.strikeOrder[this.state.currStep]){
        this.state.currStep+=1;
        this.state.currPlayer = (this.state.currPlayer+1)%2;
        this.state.strikedStages.push([]);
      }
    } else {
      if(this.state.strikedStages[this.state.currStep].length === this.state.ruleset.banCount){
        this.state.currStep+=1;
        this.state.currPlayer = (this.state.currPlayer+1)%2;
        this.state.strikedStages.push([]);
      }
    }

    if(this.state.currGame === 0 && this.state.currStep >= this.state.ruleset.strikeOrder.length){
      let selectedStage = this.state.ruleset.neutralStages.find((stage)=>!this.IsStageStriked(stage.name))
      this.state.selectedStage = selectedStage.name;
      this.state.stagesPicked.push(selectedStage.name);
    }

    this.setState(this.state);
    console.log(this.state)
  }

  MatchWinner(id){
    this.state.currGame+=1;
    this.state.currStep=0;

    this.state.stagesWon[id].push(this.state.selectedStage);

    this.state.currPlayer = id;
    this.state.strikedStages = [[]];
    this.state.selectedStage = null;

    this.state.lastWinner = id;

    this.setState(this.state);
  }

  GetStrikeNumber(){
    if(this.state.currGame == 0){
      return this.state.ruleset.strikeOrder[this.state.currStep];
    } else {
      return this.state.ruleset.banCount;
    }
  }

  componentDidMount() {
    fetch('http://127.0.0.1:5000/ruleset')
    .then(res => res.json())
    .then((data) => {
      this.setState({ ruleset: data })
      this.Initialize();
    })
    .catch(console.log)

    window.setInterval(()=>this.UpdateStream(), 1000);
  }

  UpdateStream(){
    let allStages = this.state.currGame === 0 ? this.state.ruleset.neutralStages : this.state.ruleset.neutralStages.concat(this.state.ruleset.counterpickStages);
    let stageMap = {};

    allStages.forEach(stage => {
      stageMap[stage.codename] = stage;
    });

    let data = {
      "dsr": this.GetBannedStages().map((stage)=>this.GetStage(stage).codename),
      "playerTurn": null,
      "selected": this.GetStage(this.state.selectedStage),
      "stages": stageMap,
      "striked": this.state.ruleset.neutralStages.concat(this.state.ruleset.counterpickStages).filter((stage)=>this.IsStageStriked(stage.name)).map((stage)=>stage.codename)
    }

    fetch("http://127.0.0.1:5000/post", {
      method: "POST",
      body: JSON.stringify(data),
      contentType: "application/json",
    });
  }

  render() {
    return (
      <>
        {this.state.ruleset ?
          <div style={{textAlign: "center"}}>
            <div>
              Game: {this.state.currGame+1}
            </div>
            <div>
              Player: {this.state.currPlayer+1}
            </div>
            <div>
              {this.state.currGame > 0 && this.state.currStep > 0 ?
                <>Player {this.state.currPlayer+1}, pick a stage</>
                :
                <>Player {this.state.currPlayer+1}, ban {this.GetStrikeNumber()} stage(s)</>
              }
            </div>
            <div className="container">
              <>
                {
                  this.state.ruleset.neutralStages.map((stage)=>(
                    <div class="stage-container" onClick={()=>this.StageClicked(stage)} style={{
                    }}>
                      <div class="stage-icon" style={{backgroundImage: `url('http://127.0.0.1:5000/${stage.path}')`}}>
                        {this.IsStageStriked(stage.name) ?
                          <div className='stamp stage-striked'></div>
                          :
                          null
                        }
                        {this.IsStageBanned(stage.name) ?
                          <div className='stamp stage-dsr'></div>
                          :
                          null
                        }
                        {this.state.selectedStage === stage.name ?
                          <div className='stamp stage-selected'></div>
                          :
                          null
                        }
                        <div class="stage-name">
                          <div class="text">
                            {stage.name}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                }
              </>
            </div>
            {this.state.currGame > 0 ?
              <div className="container">
                <>
                  {
                    this.state.ruleset.counterpickStages.map((stage)=>(
                      <div class="stage-container" onClick={()=>this.StageClicked(stage)} style={{
                      }}>
                        <div class="stage-icon" style={{backgroundImage: `url('http://127.0.0.1:5000/${stage.path}')`}}>
                          {this.IsStageStriked(stage.name) ?
                            <div className='stamp stage-striked'></div>
                            :
                            null
                          }
                          {this.IsStageBanned(stage.name) ?
                            <div className='stamp stage-dsr'></div>
                            :
                            null
                          }
                          {this.state.selectedStage === stage.name ?
                            <div className='stamp stage-selected'></div>
                            :
                            null
                          }
                          <div class="stage-name">
                            <div class="text">
                              {stage.name}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))
                  }
                </>
              </div>
              :
              null
            }
            <div>
              <button onClick={()=>this.ConfirmClicked()}>Confirm</button>
              <button onClick={()=>this.Initialize()}>Reset</button>
            </div>
            <div>
              <button onClick={()=>this.MatchWinner(0)}>p1 won</button>
              <button onClick={()=>this.MatchWinner(1)}>p2 won</button>
            </div>
          </div>
        :
          null
        }
      </>
    );
  }
}

export default App;
