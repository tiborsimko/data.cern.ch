import React, { useState } from "react";
import PropTypes from "prop-types";
import { Button, Card, Form, Input, Modal, Radio, Typography } from "antd";

import ReviewList from "./ReviewList";

const Reviews = ({
  review,
  draft_id,
  reviewDraft,
  reviewPublished,
  isReviewingPublished,
  publishedReviewError,
  publishedReviewLoading,
  draftReviewLoading,
  draftReviewError,
  action = "add"
}) => {
  const [showModal, setShowModal] = useState(false);
  const [showError, setShowError] = useState(false);
  const [showReviewsModal, setShowReviewsModal] = useState(false);
  const [form] = Form.useForm();
  const closeModal = () => {
    setShowModal(false);
    form.resetFields();
  };

  // if the draft is not reviewable then return null
  if (!review) return null;

  return (
    <React.Fragment>
      <Modal
        visible={showModal}
        title="Add new Review"
        okText="Submit Review"
        okButtonProps={{
          onClick: () => form.submit(),
          loading: isReviewingPublished
            ? publishedReviewLoading
            : draftReviewLoading,
          "data-cy": "submitReview"
        }}
        onCancel={() => setShowModal(false)}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            comment: "",
            reviewType: null
          }}
          onFinish={values => {
            isReviewingPublished
              ? reviewPublished({
                  body: values.comment,
                  type: values.reviewType
                }).then(response => {
                  response.error ? setShowError(true) : closeModal();
                })
              : reviewDraft(
                  draft_id,
                  {
                    body: values.comment,
                    type: values.reviewType
                  },
                  "submitted"
                ).then(response => {
                  response.error ? setShowError(true) : closeModal();
                });
          }}
        >
          <Form.Item
            label="Review Type"
            name="reviewType"
            data-cy="reviewOptions"
            rules={[{ required: true }]}
          >
            <Radio.Group buttonStyle="solid">
              <Radio.Button value="approved">Approve</Radio.Button>
              <Radio.Button value="request_changes">
                Request Changes
              </Radio.Button>
              <Radio.Button value="declined">Decline</Radio.Button>
            </Radio.Group>
          </Form.Item>
          <Form.Item
            label="Review Comment"
            rules={[{ required: true }]}
            name="comment"
          >
            <Input.TextArea
              data-cy="reviewAddComment"
              placeholder="add your comment..."
              rows={4}
            />
          </Form.Item>
        </Form>
        {showError && (
          <Typography.Text>
            {isReviewingPublished
              ? publishedReviewError && publishedReviewError.message
              : draftReviewError && draftReviewError.message}
          </Typography.Text>
        )}
      </Modal>
      <Card
        title="Reviews"
        extra={
          <Button
            data-cy="reviewShowModal"
            type="primary"
            onClick={() => setShowModal(true)}
          >
            Add Review
          </Button>
        }
        onCancel={() => setShowReviewsModal(false)}
      >
        <ReviewList
          draft_id={draft_id}
          review={review}
          isReviewingPublished={isReviewingPublished}
          reviewPublished={reviewPublished}
          reviewDraft={reviewDraft}
        />
      </Modal>
      {isReviewingPublished ? (
        action == "add" ? (
          <Button onClick={() => setShowModal(true)}>Add Review</Button>
        ) : (
          <Button onClick={() => setShowReviewsModal(true)}>
            Show Reviews
          </Button>
        )
      ) : (
        <Card
          title="Reviews"
          extra={
            <Button type="primary" onClick={() => setShowModal(true)}>
              Add Review
            </Button>
          }
        >
          <ReviewList
            draft_id={draft_id}
            review={review}
            isReviewingPublished={isReviewingPublished}
            reviewPublished={reviewPublished}
            reviewDraft={reviewDraft}
          />
        </Card>
      )}
    </React.Fragment>
  );
};

Reviews.propTypes = {
  review: PropTypes.object,
  draft_id: PropTypes.string,
  reviewDraft: PropTypes.func,
  reviewPublished: PropTypes.func,
  isReviewingPublished: PropTypes.bool,
  publishedReviewLoading: PropTypes.bool,
  draftReviewLoading: PropTypes.bool,
  publishedReviewError: PropTypes.string,
  draftReviewError: PropTypes.string,
  action: PropTypes.string
};

export default Reviews;
