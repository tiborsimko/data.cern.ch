import React from "react";
import PropTypes from "prop-types";

import { connect } from "react-redux";

import Box from "grommet/components/Box";

import { toggleFilemanagerLayer, selectPath } from "../../../../actions/files";

import DropzoneUploader from "./DropzoneUploader";

import Modal from "../../../partials/Modal";

class DepositFileManager extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      selected: null,
      formData: []
    };
  }

  _onDirectoryClick = path => {
    this.props.selectPath(path, "dir");
  };

  _onFileClick = path => {
    this.props.selectPath(path, "file");
    this.props.selectableActionLayer(path);
  };

  // TODO: this code is commented due to updates
  // most likely it will be used again when the upload files will examined closely

  // _renderSidebar = () => {
  //   return (
  //     <Box flex={false} size={{ width: "medium" }}>
  //       <Box flex={false} pad="small" colorIndex="light-1" separator="bottom">
  //         <Label size="medium" margin="none">
  //           File Manager
  //         </Label>
  //       </Box>
  //       <Box flex={true} margin={{ top: "small", right: "small" }}>
  //         <FileTree
  //           files={this.props.files.toJS()}
  //           onDirectoryClick={
  //             this.props.selectableActionLayer ? this._onDirectoryClick : null
  //           }
  //           onFileClick={
  //             this.props.selectableActionLayer ? this._onFileClick : null
  //           }
  //         />
  //       </Box>

  //       {this.props.selectableActionLayer ? (
  //         <Box
  //           colorIndex="light-2"
  //           direction="row"
  //           flex={false}
  //           pad="small"
  //           separator="top"
  //         >
  //           <Box>
  //             <Label size="small">
  //               <strong>
  //                 {this.props.message
  //                   ? this.props.message
  //                   : "Please select a file from the list, to add it to the field"}
  //               </strong>
  //             </Label>
  //             {this.props.pathSelected &&
  //               this.props.pathSelected.type == "file" && (
  //                 <Box>
  //                   <Label size="small">
  //                     <strong>Selected file:</strong>{" "}
  //                     {this.props.pathSelected && this.props.pathSelected.path}
  //                   </Label>
  //                 </Box>
  //               )}
  //             <Box
  //               colorIndex="light-2"
  //               margin={{ top: "small" }}
  //               pad={{ between: "small" }}
  //               direction="row"
  //               flex={false}
  //             >
  //               <Button
  //                 primary
  //                 label="Add to field"
  //                 onClick={this.props.pathSelected ? this.props.onSelect : null}
  //               />
  //               <Button
  //                 label="Cancel"
  //                 critical
  //                 onClick={this.props.toggleFilemanagerLayer}
  //               />
  //             </Box>
  //           </Box>
  //         </Box>
  //       ) : null}
  //     </Box>
  //   );
  // };

  render() {
    return this.props.activeLayer ? (
      <Modal onClose={this.props.toggleFilemanagerLayer} flush>
        <Box size="medium">
          <Box flex={true}>
            <Box flex={true} direction="row">
              <Box flex={true} colorIndex="grey-4">
                <DropzoneUploader />
              </Box>
            </Box>
          </Box>
        </Box>
      </Modal>
    ) : null;
  }
}

DepositFileManager.propTypes = {
  activeLayer: PropTypes.bool,
  toggleFilemanagerLayer: PropTypes.func,
  selectableActionLayer: PropTypes.func,
  files: PropTypes.object,
  active: PropTypes.number,
  message: PropTypes.string,
  selectPath: PropTypes.func,
  pathSelected: PropTypes.object,
  onSelect: PropTypes.func
};

function mapStateToProps(state) {
  return {
    activeLayer: state.draftItem.get("fileManagerActiveLayer"),
    active: state.draftItem.get("fileManagerLayerActiveIndex"),
    selectableLayer: state.draftItem.get("fileManagerLayerSelectable"),
    selectableActionLayer: state.draftItem.get(
      "fileManagerLayerSelectableAction"
    ),
    pathSelected: state.draftItem.get("pathSelected")
  };
}

function mapDispatchToProps(dispatch) {
  return {
    toggleFilemanagerLayer: () => dispatch(toggleFilemanagerLayer()),
    selectPath: (path, type) => dispatch(selectPath(path, type))
  };
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(DepositFileManager);
